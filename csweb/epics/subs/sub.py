# coding=UTF-8
'''
EPICS Subscription Abstract Classes
'''


from ...util import log

from ...util.dist import DistributingProtocol
from ...util.dist import DistributingProtocolFactory
from ...util.dist import DistributingTransport

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsSubscription:

    
    def __init__(self, subkey, subscriptions):
        self._subkey = subkey
        self._subscriptions = subscriptions
        self._subscriptions[self._subkey] = self
        self._protocolFactory = None # override in superclass


    def __str__(self):
        return self._subkey


    def unsubscribe(self):
        log.msg("EpicsSubscription: unsubscribe: %(pv)s -> %(s)s", pv=self._subkey, s=self._subscriptions[self._subkey], logLevel=_DEBUG)
        del self._subscriptions[self._subkey]


    def _connCallback(self, protocol):
        log.msg("EpicsSubscription: _connCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
    
        
    def _connErrback(self, fail=None):
        log.err("EpicsSubscription: _connErrback: Client connection error, so unsubscribe!", failure=fail)
        self.unsubscribe()

  
    def addProtocolFactory(self, protocolFactory):
        return self._protocolFactory.addProtocolFactory(protocolFactory)


class EpicsSubscriptionCanceller:

    def __init__(self, subscription):
        self._subscription = subscription
        self.cancelled = False


    def cancel(self, deferred):
        self.cancelled = True
        if not deferred.called:
            deferred.errback(Exception("Connection to '%s' canncelled." % (self._subscription,)))


class EpicsSubscriptionProtocolFactory(DistributingProtocolFactory):


    def __init__(self, subscription):
        DistributingProtocolFactory.__init__(self, [])
        self._subscription = subscription
        self._protocol = None


    def addProtocolFactory(self, protocolFactory):
        canceller = EpicsSubscriptionCanceller(self._subscription)
        deferred = defer.Deferred(canceller.cancel)
        if self._protocol is None:
            self._protocolFactories.append((deferred, canceller, protocolFactory))
        else:
            reactor.callLater(0, self._protocol.addProtocolFactory, deferred, canceller, protocolFactory)
        return deferred


    def buildProtocol(self, addr):
        for args in self._protocolFactories:
            log.msg("EpicsSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
            self._protocol.addProtocolFactory(*args)
        return self._protocol


class EpicsSubscriptionProtocol(DistributingProtocol):


    def __init__(self, address, subscription):
        DistributingProtocol.__init__(self, address, [])
        self._subscription = subscription
        self._data = None
    

    def addProtocolFactory(self, deferred, canceller, protocolFactory):
        if canceller.cancelled:
            return None

        protocol = protocolFactory.buildProtocol(self._address)
        log.msg('EpicsSubscriptionProtocol: addProtocolFactory: Append %(p)s (length: %(l)d+1)', p=protocol, l=len(self._protocols), logLevel=_DEBUG)
        self._protocols.append(protocol)
        deferred.callback(protocol)

        if self.transport is not None:
            transport = EpicsSubscriptionTransport(self.transport, protocol, self)
            log.msg('EpicsSubscriptionProtocol: addProtocolFactory: Connected so call makeConnection %(t)s', t=transport, logLevel=_TRACE)
            protocol.makeConnection(transport)
            if self._connected:
                protocol.connectionMade()
                if self._data is not None:
                    protocol.dataReceived(self._data)

        else:
            log.msg('EpicsSubscriptionProtocol: addProtocolFactory: Not connected so do NOT call makeConnection', logLevel=_TRACE)
    
        return protocol


    def removeProtocol(self, protocol):
        if protocol in self._protocols:
            log.msg('EpicsSubscriptionProtocol: removeProtocol: Remove protocol: %(p)s', p=protocol, logLevel=_DEBUG)
            protocol.connectionLost("Connection closed cleanly")
            self._protocols.remove(protocol)

            if len(self._protocols) == 0:
                log.msg('EpicsSubscriptionProtocol: removeProtocol: No protocols remaining, so loseConnection', logLevel=_DEBUG)
                self.transport.loseConnection()
                self._subscription.unsubscribe()
            
        else:
            log.msg('EpicsSubscriptionProtocol: removeProtocol: Protocol not found %(p)s', p=protocol, logLevel=_WARN)


    def dataReceived(self, data):
        DistributingProtocol.dataReceived(self, data)


    def makeConnection(self, transport):
        self.transport = transport
        log.msg('EpicsSubscriptionProtocol: makeConnection: Transport is %(t)s', t=transport, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('EpicsSubscriptionProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.makeConnection(EpicsSubscriptionTransport(transport, protocol, self))


    def float_value_from_data(self, data):
        if 'value' not in data:
            log.msg('_EpicsFilterSubscriptionProtocol: _value_from_data_recieved: Data does not contain "value".', logLevel=_WARN)
            return None
        
        try:
            return float(data['value'])
        except ValueError as error:
            log.msg('_EpicsFilterSubscriptionProtocol: _value_from_data_recieved: Value error: %(e)s', e=error, logLevel=_WARN)
            return None


class EpicsSubscriptionTransport(DistributingTransport):
    
    def __init__(self, transport, protocol, epicsProtocol):
        DistributingTransport.__init__(self, transport)
        self._epicsProtocol = epicsProtocol
        self._protocol = protocol


    def loseConnection(self):
        log.msg("EpicsSubscriptionTransport: loseConnection: Remove protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        self._epicsProtocol.removeProtocol(self._protocol)
