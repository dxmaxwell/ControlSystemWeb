# coding=UTF-8
'''
Send SMS notifications on events.
'''

from .. import device

from ..util import log

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class SMSNotifier:

    def __init__(self, smsAgent, fromNumber):
        self._smsAgent = smsAgent        
        self._fromNumber = fromNumber
        self._subscriptions = {}


    def register(self, url, dest):
        if url not in self._subscriptions:
            log.msg("SMSNotifier: register: No subsciption for URL %(r)s", r=url, logLevel=_DEBUG)
            protocolFactory = _SMSNotifierSubscriptionProtocolFactory(url, self)
            deferred = device.subscribe(url, protocolFactory)
            subscription = _SMSNotifierSubscription(deferred)
            log.msg("SMSNotifier: register: Add subsciption %(s)s", s=subscription, logLevel=_DEBUG)
            self._subscriptions[url] = subscription
        else:
            log.msg("SMSNotifier: register: Subsciption found for URL %(r)s", r=url, logLevel=_DEBUG)
            subscription = self._subscriptions[url]
        subscription.addDestination(dest)


    def notify(self, url, data, destinations):

        msg = data['pvname'] + ": "
        if 'char_value' in data:
            msg += data['char_value'] 
        elif 'value' in data:
            msg += str(data['value'])
        else:
            msg += "(UNKNOWN)"

        log.msg("SMSNotifier: notify: Message: '%(m)s'", m=msg, logLevel=_DEBUG)

        for dest in destinations:
            log.msg("SMSNotifier: notify: Destination: %(d)s", d=dest, logLevel=_DEBUG)
            smsDeferred = self._smsAgent.send(dest, self._fromNumber, msg)
            smsDeferred.addCallback(self._notify_callback)
            smsDeferred.addErrback(self._notify_errback)


    def _notify_callback(self, result):
        log.msg("SMSNotifier: _notify_callback: Sending SMS successful %(r)s", r=result, logLevel=_TRACE)


    def _notify_errback(self, failure):
        log.msg("SMSNotifier: _notify_errback: Error while sending SMS: %(f)s", f=failure.value, logLevel=_WARN)



class _SMSNotifierSubscription:

    def __init__(self, deferred):
        self._protocol = None
        self._deferred = deferred
        self._deferred.addCallback(self._subscribeCallback)
        self._deferred.addErrback(self._subscribeErrback)
        self._destinations = []


    def addDestination(self, dest):
        if self._protocol is not None:
            self._protocol.addDestination(dest)
        else:
            self._destinations.append(dest)


    def _subscribeCallback(self, protocol):
        log.msg("_SMSNotifierSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_TRACE)
        self._protocol = protocol
        for dest in self._destinations:
            self._protocol.addDestination(dest)
        del self._destinations[:]
        
        
    def _subscribeErrback(self, failure):
        log.msg("_SMSNotifierSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_WARN)



class _SMSNotifierSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier
        self._destinations = []


    def addDestination(self, dest):
        if dest is None:
            log.msg("_SMSNotifierSubscriptionProtocol: addDestination: Destination number is None", logLevel=_WARN)
        else:
            self._destinations.append(dest)
    

    def dataReceived(self, data):
        log.msg("_SMSNotifierSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_TRACE)
        self._notifier.notify(self._url, data, self._destinations)
        


class _SMSNotifierSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol Factory
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier


    def buildProtocol(self, addr):
        return _SMSNotifierSubscriptionProtocol(self._url, self._notifier)
