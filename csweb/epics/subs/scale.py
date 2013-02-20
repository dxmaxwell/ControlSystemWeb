'''
EPICS Scale (and Offset) Subscription
'''

import math

from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ...util import log

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN



class EpicsScaleSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsScaleSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsScaleSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsScaleSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsScaleSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsScaleSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, value, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._value = value
    

    def dataReceived(self, data):
        value = self.float_value_from_data(data)
        if value is not None:
            log.msg("_EpicsScaleSubscriptionProtocol: dataReceived: Scale: %(s)s", s=self._value, logLevel=_TRACE)
            data = dict(data) # Important to copy the dictionary before modification.
            value *= self._value
            data["value"] = value
            self.refresh_char_value_from_data(data, value)
        else:
            log.msg("_EpicsScaleSubscriptionProtocol: dataReceived: Scale: Value is None", logLevel=_WARN)
        EpicsSubscriptionProtocol.dataReceived(self, data)



class EpicsOffsetSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsOffsetSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsOffsetSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsOffsetSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsOffsetSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsOffsetSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, value, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._value = value
    

    def dataReceived(self, data):
        value = self.float_value_from_data(data)
        if value is not None:
            log.msg("_EpicsOffsetSubscriptionProtocol: dataReceived: Offset: %(o)s", o=self._value, logLevel=_TRACE)
            data = dict(data) # Important to copy the dictionary before modification.
            value += self._value
            data["value"] = value
            self.refresh_char_value_from_data(data, value)
        else:
            log.msg("_EpicsOffsetSubscriptionProtocol: dataReceived: Offset: Value is None", logLevel=_WARN)
        EpicsSubscriptionProtocol.dataReceived(self, data)
