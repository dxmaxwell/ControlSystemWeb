# coding=UTF-8
'''
ABC for sending notifications on events.
'''

import datetime

from .. import device

from ..util import log, dateutil

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_INFO = log.INFO
_WARN = log.WARN


class Notifier:

    def __init__(self):
        self._subscriptions = {}


    def register(self, url, dest, expiry=None):
        log.msg("Notifier: register: URL:%(r)s, Dest:%(d)s, Expiry:%(e)s", r=url, d=dest, e=expiry, logLevel=_DEBUG)
        if url not in self._subscriptions:
            log.msg("Notifier: register: No subsciption for URL %(r)s", r=url, logLevel=_TRACE)
            protocolFactory = _NotifierSubscriptionProtocolFactory(url, self)
            deferred = device.subscribe(url, protocolFactory)
            subscription = _NotifierSubscription(deferred)
            log.msg("Notifier: register: Add subsciption %(s)s", s=subscription, logLevel=_TRACE)
            self._subscriptions[url] = subscription
        else:
            log.msg("Notifier: register: Subsciption found for URL %(r)s", r=url, logLevel=_TRACE)
            subscription = self._subscriptions[url]
        subscription.addDestination(dest, self._coerse_expiry(expiry))
 


    def notify(self, url, data, destinations):
        log.msg("Notifier: notify: Abstract implementation. Should be overridden by subclass", logLevel=_WARN)


    def _notifyCallback(self, result):
        log.msg("Notifier: _notifyCallback: Sending notification successful: %(r)s", r=result, logLevel=_TRACE)


    def _notifyErrback(self, failure):
        log.msg("Notifier: _notifyErrback: Error while sending notification: %(f)s", f=failure, logLevel=_WARN)


    def _coerse_expiry(self, expiry):
        dt = datetime.datetime.max
        if expiry is not None:          
            try:
                dt = dateutil.coerse(expiry, defaultTime=datetime.time.max, defaultDate=datetime.date.today())
            except ValueError:
                pass
        return dt
    

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
        self._destinations = {}


    def addDestination(self, dest, expiry):
        if self._protocol is not None:
            self._protocol.addDestination(dest, expiry)
        elif dest is not None:
            if dest not in self._destinations:
                log.msg("_NotifierSubscription: addDestination: Add destination: %(d)s (%(e)s)", d=dest, e=expiry, logLevel=_TRACE)
            else:
                log.msg("_NotifierSubscription: addDestination: Update destination: %(d)s (%(e)s)", d=dest, e=expiry, logLevel=_TRACE)
            self._destinations[dest] = expiry
        else:
            log.msg("_NotifierSubscription: addDestination: Destination is None", logLevel=_WARN)


    def _subscribeCallback(self, protocol):
        log.msg("_NotifierSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_TRACE)
        self._protocol = protocol
        for dest, expiry in self._destinations.iteritems():
            self._protocol.addDestination(dest, expiry)
        self._destinations.clear()
        
        
    def _subscribeErrback(self, failure):
        log.msg("_NotifierSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_WARN)



class _NotifierSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier
        self._destinations = {}
        self._data = None


    def addDestination(self, dest, expiry):
        if dest is not None:
            if dest not in self._destinations:
                log.msg("_NotifierSubscriptionProtocol: addDestination: Add destination: %(d)s (%(e)s)", d=dest, e=expiry, logLevel=_TRACE)
                self._notify({ dest:expiry })
            else:
                log.msg("_NotifierSubscriptionProtocol: addDestination: Update destination: %(d)s (%(e)s)", d=dest, e=expiry, logLevel=_TRACE)
            self._destinations[dest] = expiry
        else:
            log.msg("_NotifierSubscriptionProtocol: addDestination: Destination is None", logLevel=_WARN)
    

    def dataReceived(self, data):
        log.msg("_NotifierSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_TRACE)
        self._data = dict(data)
        self._notify(self._destinations)


    def _notify(self, destinations):
        if self._data is not None:
            notifydestinations = []
            now = datetime.datetime.now()
            for dest, expiry in destinations.iteritems():
                if now <= expiry:
                    log.msg("_NotifierSubscriptionProtocol: _notify: Destination is valid: %(n)s <= %(e)s", n=now, e=expiry, logLevel=_TRACE)
                    notifydestinations.append(dest)
                else:
                    log.msg("_NotifierSubscriptionProtocol: _notify: Destination is not valid: %(n)s > %(e)s", n=now, e=expiry, logLevel=_TRACE)
            if len(notifydestinations) > 0:
                log.msg("_NotifierSubscriptionProtocol: _notify: Valid destinations found.", logLevel=_TRACE)
                self._notifier.notify(self._url, self._data, notifydestinations)
            else:
                log.msg("_NotifierSubscriptionProtocol: _notify: No valid destinations found.", logLevel=_TRACE)
        else:
            log.msg("_NotifierSubscriptionProtocol: _notify: No data recieved. Unable to notify.", logLevel=_TRACE)


class _NotifierSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol Factory
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier


    def buildProtocol(self, addr):
        return _NotifierSubscriptionProtocol(self._url, self._notifier)
