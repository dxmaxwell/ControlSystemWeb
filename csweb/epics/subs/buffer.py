# coding=UTF-8
'''
EPICS Buffer Subscription
'''


from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ...util import log

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsBufferSubscription(EpicsSubscription):
    
    def __init__(self, sub, size, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsBufferSubscriptionProtocolFactory(size, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsBufferSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, size, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._size = size


    def buildProtocol(self, addr):
        self._protocol = _EpicsBufferSubscriptionProtocol(addr, self._size, self._subscription)
        log.msg("_EpicsBufferSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsBufferSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, size, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._size = size
        
    
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
        EpicsSubscriptionProtocol.dataReceived(self, data)
