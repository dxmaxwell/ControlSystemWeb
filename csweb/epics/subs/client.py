# coding=UTF-8
'''
Epics Client Subscription
'''


from ..client import ProcessVariableClientEndpoint

from ...util import log, dist

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsClientSubscription:

    
    def __init__(self, pvname, subkey, subscriptions):
        self._subkey = subkey
        self._subscriptions = subscriptions
        self._subscriptions[self._subkey] = self
        self._protocolFactory = _EpicsClientSubscriptionProtocolFactory(self)
        self._pvclient = ProcessVariableClientEndpoint(pvname)
        self._pvclient.connect(self._protocolFactory)


    def __str__(self):
        return self._subkey


    def unsubscribe(self):
        log.msg("EpicsClientSubscription: unsubscribe: %(pv)s -> %(s)s", pv=self._subkey, s=self._subscriptions[self._subkey], logLevel=_DEBUG)
        del self._subscriptions[self._subkey]


    def _connCallback(self, protocol):
        log.msg("EpicsClientSubscription: _connCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
    
        
    def _connErrback(self, fail=None):
        log.err("EpicsClientSubscription: _connErrback: Client connection error, so unsubscribe!", failure=fail)
        self.unsubscribe()

  
    def addProtocolFactory(self, protocolFactory):
        return self._protocolFactory.addProtocolFactory(protocolFactory)


class _EpicsClientSubscriptionCanceller:

    def __init__(self, subscription):
        self._subscription = subscription
        self.cancelled = False

    def cancel(self, deferred):
        self.cancelled = True
        if not deferred.called:
            deferred.errback(Exception("Connection to '%s' canncelled." % (self._subscription,)))


class _EpicsClientSubscriptionProtocolFactory(dist.DistributingProtocolFactory):
     
    def __init__(self, subscription):
        dist.DistributingProtocolFactory.__init__(self, [])
        self._subscription = subscription
        self._protocol = None


    def addProtocolFactory(self, protocolFactory):
        canceller = _EpicsClientSubscriptionCanceller(self._subscription)
        deferred = defer.Deferred(canceller.cancel)
        if self._protocol is None:
            self._protocolFactories.append((deferred, canceller, protocolFactory))
        else:
            reactor.callLater(0, self._protocol.addProtocolFactory, deferred, canceller, protocolFactory)
        return deferred


    def buildProtocol(self, addr):
        self._protocol = _EpicsClientSubscriptionProtocol(addr, self._subscription)
        log.msg("_EpicsClientSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        for args in self._protocolFactories:
            self._protocol.addProtocolFactory(*args)
        return self._protocol


class _EpicsClientSubscriptionProtocol(dist.DistributingProtocol):

    def __init__(self, address, subscription):
        dist.DistributingProtocol.__init__(self, address, [])
        self._subscription = subscription
        self._data = None
    

    def addProtocolFactory(self, deferred, canceller, protocolFactory):
        if canceller.cancelled:
            return None

        protocol = protocolFactory.buildProtocol(self._address)
        log.msg('_EpicsClientSubscriptionProtocol: addProtocolFactory: Append %(p)s (length: %(l)d+1)', p=protocol, l=len(self._protocols), logLevel=_DEBUG)
        self._protocols.append(protocol)
        deferred.callback(protocol)

        if self.transport is not None:
            transport = _EpicsClientSubscriptionTransport(self.transport, protocol, self)
            log.msg('_EpicsClientSubscriptionProtocol: addProtocolFactory: Connected so call makeConnection %(t)s', t=transport, logLevel=_TRACE)
            protocol.makeConnection(transport)
            if self._connected:
                protocol.connectionMade()
                if self._data is not None:
                    protocol.dataReceived(self._data)

        else:
            log.msg('_EpicsClientSubscriptionProtocol: addProtocolFactory: Not connected so do NOT call makeConnection', logLevel=_TRACE)
    
        return protocol


    def removeProtocol(self, protocol):
        if protocol in self._protocols:
            log.msg('_EpicsClientSubscriptionProtocol: removeProtocol: Remove protocol: %(p)s', p=protocol, logLevel=_DEBUG)
            protocol.connectionLost("Connection closed cleanly")
            self._protocols.remove(protocol)

            if len(self._protocols) == 0:
                log.msg('_EpicsClientSubscriptionProtocol: removeProtocol: No protocols remaining, so loseConnection', logLevel=_DEBUG)
                self.transport.loseConnection()
                self._subscription.unsubscribe()
            
        else:
            log.msg('_EpicsClientSubscriptionProtocol: removeProtocol: Protocol not found %(p)s', p=protocol, logLevel=_WARN)


    def dataReceived(self, data):
        self._data = data
        dist.DistributingProtocol.dataReceived(self, data)
    

    def makeConnection(self, transport):
        self.transport = transport
        log.msg('_EpicsClientSubscriptionProtocol: makeConnection: Transport is %(t)s', t=transport, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('_EpicsClientSubscriptionProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.makeConnection(_EpicsClientSubscriptionTransport(transport, protocol, self))


class _EpicsClientSubscriptionTransport(dist.DistributingTransport):
    
    def __init__(self, transport, protocol, epicsProtocol):
        dist.DistributingTransport.__init__(self, transport)
        self._epicsProtocol = epicsProtocol
        self._protocol = protocol


    def loseConnection(self):
        log.msg("_EpicsClientSubscriptionWrappingTransport: loseConnection: Remove protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        self._epicsProtocol.removeProtocol(self._protocol)
