'''
EPICS Filter Subscription
'''

import math

from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ...util import log

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class _EpicsFilterSubscriptionProtocol(EpicsSubscriptionProtocol):

    NaN = float('nan')

    def __init__(self, address, value, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._value = value


    def _value_from_data_recieved(self, data):
        if 'value' not in data:
            log.msg('_EpicsFilterSubscriptionProtocol: _value_from_data_recieved: Data does not contain "value".', logLevel=_WARN)
            return self.NaN
        
        try:
            value = float(data['value'])
        except ValueError as error:
            log.msg('_EpicsFilterSubscriptionProtocol: _value_from_data_recieved: Value error: %(e)s', e=error, logLevel=_WARN)
            return self.NaN

        return value


class EpicsHighEdgeSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsHighEdgeSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsHighEdgeSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsHighEdgeSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsHighEdgeSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsHighEdgeSubscriptionProtocol(_EpicsFilterSubscriptionProtocol):

    def __init__(self, address, value, subscription):
        _EpicsFilterSubscriptionProtocol.__init__(self, address, value, subscription)
        self._data = False
    

    def dataReceived(self, data):
        value = self._value_from_data_recieved(data)
        if math.isnan(value):
            return

        result = (value >= self._value)
        if result == True:
            log.msg("_EpicsHighEdgeSubscriptionProtocol: dataReceived: New value >= %(v)f", v=self._value, logLevel=_TRACE)
            if self._data == False:
                log.msg("_EpicsHighEdgeSubscriptionProtocol: dataReceived: High edge transition reached.", logLevel=_TRACE)
                EpicsSubscriptionProtocol.dataReceived(self, data)
        else:
            log.msg("_EpicsHighEdgeSubscriptionProtocol: dataReceived: New value < %(v)f", v=self._value, logLevel=_TRACE)
        self._data = result


class EpicsLowEdgeSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsLowEdgeSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsLowEdgeSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsLowEdgeSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsLowEdgeSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsLowEdgeSubscriptionProtocol(_EpicsFilterSubscriptionProtocol):

    def __init__(self, address, value, subscription):
        _EpicsFilterSubscriptionProtocol.__init__(self, address, value, subscription)
        self._data = False
    

    def dataReceived(self, data):
        value = self._value_from_data_recieved(data)
        if math.isnan(value):
            return

        result = (value <= self._value)    
        if result == True:
            log.msg("_EpicsLowEdgeSubscriptionProtocol: dataReceived: New value <= %(v)f", v=self._value, logLevel=_TRACE)
            if self._data == False:
                log.msg("_EpicsLowEdgeSubscriptionProtocol: dataReceived: Low edge transition reached.", logLevel=_TRACE)
                EpicsSubscriptionProtocol.dataReceived(self, data)
        else:
            log.msg("_EpicsLowEdgeSubscriptionProtocol: dataReceived: New value > %(v)f", v=self._value, logLevel=_TRACE)
        self._data = result




class EpicsThresholdSubscription(EpicsSubscription):
    
    def __init__(self, sub, value, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsThresholdSubscriptionProtocolFactory(value, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsThresholdSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     
    def __init__(self, value, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._value = value


    def buildProtocol(self, addr):
        self._protocol = _EpicsThresholdSubscriptionProtocol(addr, self._value, self._subscription)
        log.msg("_EpicsThresholdSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_TRACE)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)


class _EpicsThresholdSubscriptionProtocol(_EpicsFilterSubscriptionProtocol):

    def __init__(self, address, value, subscription):
        _EpicsFilterSubscriptionProtocol.__init__(self, address, value, subscription)


    def dataReceived(self, data):
        value = self._value_from_data_recieved(data)
        if math.isnan(value):
            return

        result = (value <= self._value)
        if self._data != result:
            EpicsSubscriptionProtocol.dataReceived(self, data)
        self._data = result

        if result == True:
            log.msg("_EpicsThresholdSubscriptionProtocol: dataReceived: New value <= %(v)f", v=self._value, logLevel=_TRACE)
        else:
            log.msg("_EpicsThresholdSubscriptionProtocol: dataReceived: New value > %(v)f", v=self._value, logLevel=_TRACE)
        if self._data != result:
                log.msg("_EpicsThresholdSubscriptionProtocol: dataReceived: Threshold reached.", logLevel=_TRACE)
                EpicsSubscriptionProtocol.dataReceived(self, data)
        self._data = result
