'''
EPICS Setter Subscription
'''

import math

from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ...util import log

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN



class EpicsSetSubscription(EpicsSubscription):
    
    def __init__(self, sub, key, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsSetSubscriptionProtocolFactory(key, value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsSetSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, key, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._key = key
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsSetSubscriptionProtocol(addr, self._key, self._value, self._subscription)
        log.msg("_EpicsSetSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsSetSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, key, value, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._key = key
        self._value = value
    

    def dataReceived(self, data):
        log.msg("_EpicsSetSubscriptionProtocol: dataReceived: Set Key:'%(k)s' to Value:'%(v)s'", k=self._key, v=self._value, logLevel=_TRACE)
        data[self._key] = self._value
        EpicsSubscriptionProtocol.dataReceived(self, data)



class EpicsSetPrecisionSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsSetPrecisionSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsSetPrecisionSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsSetPrecisionSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsSetPrecisionSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsSetPrecisionSubscriptionProtocol(EpicsSubscriptionProtocol):

    def __init__(self, address, precision, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._precision = precision
    

    def dataReceived(self, data):
        value = self.float_value_from_data(data)
        if value is not None:
            log.msg("_EpicsSetPrecisionSubscriptionProtocol: dataReceived: Set Precision: %(p)s", p=self._precision, logLevel=_TRACE)
            data["precision"] = self._precision
            data["char_value"] = str(round(value, self._precision))
        else:
            log.msg("_EpicsSetPrecisionSubscriptionProtocol: dataReceived: Set Precision: Value is None", logLevel=_WARN)
        EpicsSubscriptionProtocol.dataReceived(self, data)
