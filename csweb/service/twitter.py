# coding=UTF-8
'''
Send twitter notifications on events.

NOTE: The Twitty Twister library uses the Twitter REST API v1.0
      which to due to be depricated March 2013. This may need
      to be reimplemented using an OAuth library directly if
      no other suitable Twisted library can be found.
'''

from .. import device

from ..util import log

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from twittytwister.twitter import Twitter


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class TwitterNotifier:

    def __init__(self, consumer, token):
        self._subscriptions = {}
        self._twitter = Twitter(consumer=consumer, token=token)


    def register(self, url):
        if url not in self._subscriptions:
            log.msg("TwitterNotifier: register: No subsciption for URL %(r)s", r=url, logLevel=_DEBUG)
            protocolFactory = TwitterNotifierSubscriptionProtocolFactory(url, self)
            deferred = device.subscribe(url, protocolFactory)
            subscription = _TwitterNotifierSubscription(deferred)
            log.msg("TwitterNotifier: register: Add subsciption %(s)s", s=subscription, logLevel=_TRACE)
            self._subscriptions[url] = subscription
        else:
            log.msg("TwitterNotifier: register: Subsciption found for URL %(r)s", r=url, logLevel=_DEBUG)


    def notify(self, url, data):

        msg = self._toHashTag(data['pvname']) + " "
        if 'char_value' in data:
            msg += data['char_value'] 
        elif 'value' in data:
            msg += str(data['value'])
        else:
            msg += "(UNKNOWN)"

        log.msg("TwitterNotifier: notify: Message: %(m)s", m=msg, logLevel=_TRACE)
        twitterDeferred = self._twitter.update(msg)
        twitterDeferred.addCallback(self._notify_callback)
        twitterDeferred.addErrback(self._notify_errback)


    def _notify_callback(self, result):
        log.msg("TwitterNotifier: _notify_callback: Status update successful %(r)s", r=result, logLevel=_TRACE)


    def _notify_errback(self, err):
        log.msg("TwitterNotifier: _notify_errback: Error while updating status: %(e)s", e=err, logLevel=_WARN)


    def _toHashTag(self, s):
    	return '#' + s.replace(':', '')

class _TwitterNotifierSubscription:

    def __init__(self, deferred):
        self._protocol = None
        self._deferred = deferred
        self._deferred.addCallback(self._subscribeCallback)
        self._deferred.addErrback(self._subscribeErrback)


    def _subscribeCallback(self, protocol):
        log.msg("_TwitterNotifierSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
        self._protocol = protocol
    
 	
    def _subscribeErrback(self, failure):
        log.msg("_TwitterNotifierSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_DEBUG)



class TwitterNotifierSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier
        self._dataReceived = False
    

    def dataReceived(self, data):
        log.msg("TwitterNotifierSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_DEBUG)
        # Ignore the first call that occurs when the device initially connects.
        if self._dataReceived:
            self._notifier.notify(self._url, data)
        else:
            self._dataReceived = True


class TwitterNotifierSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol Factory
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier


    def buildProtocol(self, addr):
        return TwitterNotifierSubscriptionProtocol(self._url, self._notifier)
