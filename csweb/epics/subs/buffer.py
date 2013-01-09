# coding=UTF-8
'''
EPICS Buffer Subscription
'''


from ..client import ProcessVariableClientEndpoint

from ...util import log, dist

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsBufferSubscription:

    
    def __init__(self, sub, size, subkey, subscriptions):
        self._subkey = subkey
        self._subscriptions = subscriptions
        self._subscriptions[self._subkey] = self
        self._protocolFactory = _EpicsBufferSubscriptionProtocolFactory(size, self)
        sub.addProtocolFactory(self._protocolFactory)


    def __str__(self):
        return self._subkey


    def unsubscribe(self):
        log.msg("EpicsBufferSubscription: unsubscribe: %(k)s -> %(s)s", k=self._subkey, s=self._subscriptions[self._subkey], logLevel=_DEBUG)
        del self._subscriptions[self._subkey]


    def _connCallback(self, protocol):
        log.msg("EpicsBufferSubscription: _connCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
    
        
    def _connErrback(self, fail=None):
        log.err("EpicsBufferSubscription: _connErrback: Client connection error, so unsubscribe!", failure=fail)
        self.unsubscribe()

  
    def addProtocolFactory(self, protocolFactory):
        return self._protocolFactory.addProtocolFactory(protocolFactory)


class _EpicsBufferSubscriptionCanceller:

    def __init__(self, subscription):
        self._subscription = subscription
        self.cancelled = False

    def cancel(self, deferred):
        self.cancelled = True
        if not deferred.called:
            deferred.errback(Exception("Connection to '%s' canncelled." % (self._subscription,)))


class _EpicsBufferSubscriptionProtocolFactory(dist.DistributingProtocolFactory):
     
    def __init__(self, size, subscription):
        dist.DistributingProtocolFactory.__init__(self, [])
        self._subscription = subscription
        self._protocol = None
        self._size = size


    def addProtocolFactory(self, protocolFactory):
        canceller = _EpicsBufferSubscriptionCanceller(self._subscription)
        deferred = defer.Deferred(canceller.cancel)
        if self._protocol is None:
            self._protocolFactories.append((deferred, canceller, protocolFactory))
        else:
            reactor.callLater(0, self._protocol.addProtocolFactory, deferred, canceller, protocolFactory)
        return deferred


    def buildProtocol(self, addr):
        self._protocol = _EpicsBufferSubscriptionProtocol(addr, self._size, self._subscription)
        log.msg("_EpicsBufferSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        for args in self._protocolFactories:
            self._protocol.addProtocolFactory(*args)
        return self._protocol


class _EpicsBufferSubscriptionProtocol(dist.DistributingProtocol):

    def __init__(self, address, size, subscription):
        dist.DistributingProtocol.__init__(self, address, [])
        self._subscription = subscription
        self._size = size
        self._data = None
    

    def addProtocolFactory(self, deferred, canceller, protocolFactory):
        if canceller.cancelled:
            return None

        protocol = protocolFactory.buildProtocol(self._address)
        log.msg('_EpicsBufferSubscriptionProtocol: addProtocolFactory: Append %(p)s (length: %(l)d+1)', p=protocol, l=len(self._protocols), logLevel=_DEBUG)
        self._protocols.append(protocol)
        deferred.callback(protocol)

        if self.transport is not None:
            transport = _EpicsBufferSubscriptionTransport(self.transport, protocol, self)
            log.msg('_EpicsBufferSubscriptionProtocol: addProtocolFactory: Connected so call makeConnection %(t)s', t=transport, logLevel=_TRACE)
            protocol.makeConnection(transport)
            if self._connected:
                protocol.connectionMade()
                if self._data is not None:
                    protocol.dataReceived(self._data)

        else:
            log.msg('_EpicsBufferSubscriptionProtocol: addProtocolFactory: Not connected so do NOT call makeConnection', logLevel=_TRACE)
    
        return protocol


    def removeProtocol(self, protocol):
        if protocol in self._protocols:
            log.msg('_EpicsBufferSubscriptionProtocol: removeProtocol: Remove protocol: %(p)s', p=protocol, logLevel=_DEBUG)
            # Do not unsubscribe, the buffer will live for the life of the server! Maybe a timeout is required instead.
            protocol.connectionLost("Connection closed cleanly")
            self._protocols.remove(protocol)
            
        else:
            log.msg('_EpicsBufferSubscriptionProtocol: removeProtocol: Protocol not found %(p)s', p=protocol, logLevel=_WARN)


    def dataReceived(self, data):
        if self._data == None:
            self._data = [  dict(data)  ]
        else:
            self._data.append(dict(data))
            if len(self._data) > self._size:
                self._data = self._data[1:]
        dist.DistributingProtocol.dataReceived(self, data)
    

    def makeConnection(self, transport):
        self.transport = transport
        log.msg('_EpicsSubscriptionProtocol: makeConnection: Transport is %(t)s', t=transport, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('_EpicsSubscriptionProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.makeConnection(_EpicsBufferSubscriptionTransport(transport, protocol, self))


class _EpicsBufferSubscriptionTransport(dist.DistributingTransport):
    
    def __init__(self, transport, protocol, epicsProtocol):
        dist.DistributingTransport.__init__(self, transport)
        self._epicsProtocol = epicsProtocol
        self._protocol = protocol


    def loseConnection(self):
        log.msg("_EpicsBufferSubscriptionTransport: loseConnection: Remove protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        self._epicsProtocol.removeProtocol(self._protocol)
