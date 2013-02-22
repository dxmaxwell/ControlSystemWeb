# coding=UTF-8
'''
ABC for sending notifications on events.
'''

from .. import device

from ..util import log

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class Notifier:

    def __init__(self):
        self._subscriptions = {}


    def register(self, url, dest):
        if url not in self._subscriptions:
            log.msg("Notifier: register: No subsciption for URL %(r)s", r=url, logLevel=_DEBUG)
            protocolFactory = _NotifierSubscriptionProtocolFactory(url, self)
            deferred = device.subscribe(url, protocolFactory)
            subscription = _NotifierSubscription(deferred)
            log.msg("Notifier: register: Add subsciption %(s)s", s=subscription, logLevel=_DEBUG)
            self._subscriptions[url] = subscription
        else:
            log.msg("Notifier: register: Subsciption found for URL %(r)s", r=url, logLevel=_DEBUG)
            subscription = self._subscriptions[url]
        subscription.addDestination(dest)


    def notify(self, url, data, destinations):
		log.msg("Notifier: notify: Abstract implementation. Should be overridden by subclass", logLevel=_WARN)


    def _notifyCallback(self, result):
        log.msg("Notifier: _notifyCallback: Sending notification successful: %(r)s", r=result, logLevel=_TRACE)


    def _notifyErrback(self, failure):
        log.msg("Notifier: _notifyErrback: Error while sending notification: %(f)s", f=failure, logLevel=_WARN)


    def _name_from_data(self, data, defaultName="UnknownDevice"):
        name = defaultName
        if "name" in data:
            name = str(data["name"])
        elif "pvname" in data:
            name = str(data["pvname"])
        return name


    def _str_value_from_data(self, data, defaultValue="<NAN>"):
        value = defaultValue
        if "char_value" in data:
            value = str(data["char_value"])
            if "units" in data:
                value += str(data["units"])
        elif "value" in data:
            value = str(data["value"])
            if "units" in data:
                value += str(data["units"])
        return value
        

class _NotifierSubscription:

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
        log.msg("_NotifierSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_TRACE)
        self._protocol = protocol
        for dest in self._destinations:
            self._protocol.addDestination(dest)
        del self._destinations[:]
        
        
    def _subscribeErrback(self, failure):
        log.msg("_NotifierSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_WARN)



class _NotifierSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier
        self._destinations = []


    def addDestination(self, dest):
        if dest is None:
            log.msg("_NotifierSubscriptionProtocol: addDestination: Destination number is None", logLevel=_WARN)
        else:
            self._destinations.append(dest)
    

    def dataReceived(self, data):
        log.msg("_NotifierSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_TRACE)
        self._notifier.notify(self._url, data, self._destinations)
        


class _NotifierSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol Factory
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier


    def buildProtocol(self, addr):
        return _NotifierSubscriptionProtocol(self._url, self._notifier)
