# coding=UTF-8
'''
DeviceProvider interface for EPICS PVs.

Supported URL:
    epics:ProcessVariable
'''

from urllib import urlencode
from urlparse import urlsplit, urlunsplit, parse_qsl


from .client import ProcessVariableClientEndpoint

from ..util.url import URL
from ..util import log, dist

from ..device.provider import DeviceProvider
from ..device.manager import NotSupportedError

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN

_EPICS_SCHEME = 'epics'


URL.register_scheme(_EPICS_SCHEME)


class EpicsDeviceProvider(DeviceProvider):
    '''
    Implementation of DeviceProvider interface for accessing EPICS Channel Access.
    '''

    def __init__(self):
        self._subscriptions = {}


    def subscribe(self, url, protocolFactory):
        '''
        Subscribe to the specified EPICS PV.  
        '''
        try:
            url = self._supports(url)
            log.msg("EpicsDeviceProvider: subscribe: Supported URI: %(u)s", u=url, logLevel=_DEBUG)
        except Exception as fail:
            log.msg("EpicsDeviceProvider: subscribe: Unsuppored URI: %(u)s", u=url, logLevel=_WARN)
            # return something!

        if str(url) in self._subscriptions:
            subscription = self._subscriptions[str(url)]
        else:
            pvname = URL.decode(url.path)
            subscription = _EpicsSubscription(pvname, str(url), self._subscriptions)

        return subscription.addProtocolFactory(protocolFactory)


    def _supports(self, url):
        url = URL(url)
        if url.scheme != _EPICS_SCHEME:
            raise NotSupportedError("Scheme (%s) not supported by EpicsDeviceProvider" % (result.scheme))

        url.path = url.path.strip('/')
        if url.path == '':
            raise NotSupportedError("Path is empty, process variable must be specified")

        url.merge_params()
        url.query.clear()
        return url


    def supports(self, url):
        try:
            self._supports(url)
            return True
        except NotSupportedError:
            return False


class _EpicsSubscription:

    
    def __init__(self, pvname, subkey, subscriptions):
        self._subkey = subkey
        self._subscriptions = subscriptions
        self._subscriptions[self._subkey] = self
        self._pvclient = ProcessVariableClientEndpoint(pvname)
        self._protocolFactory = _EpicsSubscriptionProtocolFactory(self)

        self._pvclient.connect(self._protocolFactory)


    def unsubscribe(self):
        log.msg("_EpicsSubscription: unsubscribe: %(pv)s -> %(s)s", pv=self._subkey, s=self._subscriptions[self._subkey], logLevel=_DEBUG)
        del self._subscriptions[self._subkey]


    def _connCallback(self, protocol):
        log.msg("_EpicsSubscription: _connCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
    
        
    def _connErrback(self, fail=None):
        log.err("_EpicsSubscription: _connErrback: Client connection error, so unsubscribe!", failure=fail)
        self.unsubscribe()

  
    def addProtocolFactory(self, protocolFactory):
        return self._protocolFactory.addProtocolFactory(protocolFactory)


class _EpicsSubscriptionCanceller:

    def __init__(self):
        self.cancelled = False

    def cancel(self, deferred):
        self.cancelled = True
        deferred.errback()


class _EpicsSubscriptionProtocolFactory(dist.DistributingProtocolFactory):
     
    def __init__(self, subscription):
        dist.DistributingProtocolFactory.__init__(self, [])
        self._subscription = subscription
        self._protocol = None


    def addProtocolFactory(self, protocolFactory):
        canceller = _EpicsSubscriptionCanceller()
        deferred = defer.Deferred(canceller.cancel)
        if self._protocol is None:
            self._protocolFactories.append((deferred, canceller, protocolFactory))
        else:
            reactor.callLater(0, self._protocol.addProtocolFactory, deferred, canceller, protocolFactory)
        return deferred


    def buildProtocol(self, addr):
        self._protocol = _EpicsSubscriptionProtocol(addr, self._subscription)
        log.msg("_EpicsSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        for args in self._protocolFactories:
            self._protocol.addProtocolFactory(*args)
        return self._protocol


class _EpicsSubscriptionProtocol(dist.DistributingProtocol):

    def __init__(self, address, subscription):
        dist.DistributingProtocol.__init__(self, address, [])
        self._subscription = subscription
        self._data = None
    

    def addProtocolFactory(self, deferred, canceller, protocolFactory):
        if canceller.cancelled:
            return None

        protocol = protocolFactory.buildProtocol(self._address)
        log.msg('DistributingPrococol: addProtocolFactory: Append %(p)s (length: %(l)d+1)', p=protocol, l=len(self._protocols), logLevel=_DEBUG)
        self._protocols.append(protocol)
        deferred.callback(protocol)

        if self.transport is not None:
            transport = _EpicsSubscriptionTransport(self.transport, protocol, self)
            log.msg('DistributingPrococol: addProtocolFactory: Connected so call makeConnection %(t)s', t=transport, logLevel=_TRACE)
            protocol.makeConnection(transport)
            if self._connected:
                protocol.connectionMade()
                if self._data is not None:
                    protocol.dataReceived(self._data)

        else:
            log.msg('DistributingPrococol: addProtocolFactory: Not connected so do NOT call makeConnection', logLevel=_TRACE)
    
        return protocol


    def removeProtocol(self, protocol):
        if protocol in self._protocols:
            log.msg('DistributingPrococol: removeProtocol: Remove protocol: %(p)s', p=protocol, logLevel=_DEBUG)
            
            if len(self._protocols) == 1:
                log.msg('DistributingPrococol: removeProtocol: No protocols remaining, so loseConnection', logLevel=_DEBUG)
                self.transport.loseConnection()
                self._subscription.unsubscribe()
            else:
                log.msg('DistributingPrococol: removeProtocol: Protocols remaining, so connectionLost', logLevel=_DEBUG)
                protocol.connectionLost("Connection closed cleanly")
            
            self._protocols.remove(protocol)
            
        else:
            log.msg('DistributingPrococol: removeProtocol: Protocol not found %(p)s', p=protocol, logLevel=_WARN)


    def dataReceived(self, data):
        self._data = data
        dist.DistributingProtocol.dataReceived(self, data)
    

    def makeConnection(self, transport):
        self.transport = transport
        log.msg('_EpicsSubscriptionProtocol: makeConnection: Transport is %(t)s', t=transport, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('_EpicsSubscriptionProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.makeConnection(_EpicsSubscriptionTransport(transport, protocol, self))


class _EpicsSubscriptionTransport(dist.DistributingTransport):
    
    def __init__(self, transport, protocol, epicsProtocol):
        dist.DistributingTransport.__init__(self, transport)
        self._epicsProtocol = epicsProtocol
        self._protocol = protocol


    def loseConnection(self):
        log.msg("_EpicsSubscriptionWrappingTransport: loseConnection: Remove protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        self._epicsProtocol.removeProtocol(self._protocol)
