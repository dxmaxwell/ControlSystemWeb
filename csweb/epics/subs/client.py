# coding=UTF-8
'''
Epics Client Subscription
'''


from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ..client import ProcessVariableClientEndpoint

from ...util import log, dist

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsClientSubscription(EpicsSubscription):

    def __init__(self, pvname, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsClientSubscriptionProtocolFactory(self)
        self._pvclient = ProcessVariableClientEndpoint(pvname)
        self._pvclient.connect(self._protocolFactory)


class _EpicsClientSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)


    def buildProtocol(self, addr):
        self._protocol = _EpicsClientSubscriptionProtocol(addr, self._subscription)
        log.msg("_EpicsClientSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsClientSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)


    def dataReceived(self, data):
        self._data = data
        EpicsSubscriptionProtocol.dataReceived(self, data)
