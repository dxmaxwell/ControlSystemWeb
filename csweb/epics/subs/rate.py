# coding=UTF-8
'''
EPICS Rate (Limit) Subscription
'''

import time

from .sub import EpicsSubscription
from .sub import EpicsSubscriptionProtocol
from .sub import EpicsSubscriptionProtocolFactory

from ...util import log

from twisted.internet import task


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class EpicsRateSubscription(EpicsSubscription):

    
    def __init__(self, sub, interval, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsRateSubscriptionProtocolFactory(interval, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsRateSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     

    def __init__(self, interval, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._interval = interval

    def buildProtocol(self, addr):
        self._protocol = _EpicsRateSubscriptionProtocol(addr, self._interval, self._subscription)
        log.msg("_EpicsRateSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)

    
class _EpicsRateSubscriptionProtocol(EpicsSubscriptionProtocol):


    def __init__(self, address, interval, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._interval = interval
        self._clock = task.LoopingCall(self._tick)

    
    def _tick(self):
        if self._data is not None:
            if 'timestamp' in self._data:
                # update the timestamp of the event #
                self._data['timestamp'] = time.time()
            EpicsSubscriptionProtocol.dataReceived(self, self._data)


    def dataReceived(self, data):
        self._data = dict(data)
        if not self._clock.running:
            self._clock.start(self._interval)


    def connectionLost(self, reason):
        EpicsSubscriptionProtocol.connectionLost(self, reason)
        if self._clock.running: self._clock.stop()





class EpicsRateLimitSubscription(EpicsSubscription):

    
    def __init__(self, sub, interval, subkey, subscriptions):
        EpicsSubscription.__init__(self, subkey, subscriptions)
        self._protocolFactory = _EpicsRateLimitSubscriptionProtocolFactory(interval, self)
        sub.addProtocolFactory(self._protocolFactory)


class _EpicsRateLimitSubscriptionProtocolFactory(EpicsSubscriptionProtocolFactory):
     

    def __init__(self, interval, subscription):
        EpicsSubscriptionProtocolFactory.__init__(self, subscription)
        self._interval = interval

    def buildProtocol(self, addr):
        self._protocol = _EpicsRateLimitSubscriptionProtocol(addr, self._interval, self._subscription)
        log.msg("_EpicsRateLimitSubscriptionProtocolFactory: buildProtocol: Built protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
        return EpicsSubscriptionProtocolFactory.buildProtocol(self, addr)

    
class _EpicsRateLimitSubscriptionProtocol(EpicsSubscriptionProtocol):


    def __init__(self, address, interval, subscription):
        EpicsSubscriptionProtocol.__init__(self, address, subscription)
        self._interval = interval
        self._clockTicked = False
        self._dataReceived = False
        self._clock = task.LoopingCall(self._tick)

    
    def _tick(self):
        if self._dataReceived:
            if 'timestamp' in self._data:
                # update the timestamp of the event #
                self._data['timestamp'] = time.time()
            EpicsSubscriptionProtocol.dataReceived(self, self._data)
            self._dataReceived = False
        else:
            self._clockTicked = True


    def dataReceived(self, data):
        self._data = dict(data)
        if not self._clock.running:
            self._clock.start(self._interval)
        if self._clockTicked:
            EpicsSubscriptionProtocol.dataReceived(self, self._data)
            self._clockTicked = False
        else:
            self._dataReceived = True


    def connectionLost(self, reason):
        EpicsSubscriptionProtocol.connectionLost(self, reason)
        if self._clock.running: self._clock.stop()
