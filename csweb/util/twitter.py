# coding=UTF-8
'''
A Twisted enabled Twitter utility.

(This could eventually become a separate library.)
'''

try:
    from cStringIO import StringIO
except:
    from  StringIO import StringIO

from ..util import log, json

from twisted.internet import defer
from twisted.python.failure import Failure


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


TWITTER_BASE_URL = 'https://api.twitter.com/1.1'


class TwitterAgent:

    def __init__(self, httpAgent):
        self._httpAgent = httpAgent


    def update(self, status):
        deferred = defer.Deferred();
        parameters = { 'status':status }
        log.msg("TwitterAgent: update: New status: %(s)s", s=status, logLevel=_TRACE)
        _TwitterUpdater(deferred, self._httpAgent, parameters)
        return deferred


class _TwitterUpdater:

    def __init__(self, deferred, httpAgent, parameters):
        self._deferred = deferred
        url = TWITTER_BASE_URL + '/statuses/update.json'
        d = httpAgent.request('POST', url, body=parameters)
        d.addCallback(self._callback)
        d.addErrback(self._errback)


    def _callback(self, response):
        log.msg("_TwitterUpdater: _callback: Response received", logLevel=_DEBUG)
        # Assume response is JSON, without checking the headers!
        try:
            body = json.parse(response.body)
        except:
            self._deferred.errback(Failure())

        try:
            if response.isSuccessful():
                self._deferred.callback(body)
            elif "errors" in body:
                for error in body["errors"]:
                    if "message" in error:
                        raise _TwitterException("Twitter Error: Message: " + error["message"])
                    if "code" in error:
                        raise _TwitterException("Twitter Error: Code: " + error["code"])
                else:
                    raise _TwitterException("Twitter Error: Unknown (2)")
            else:
               raise _TwitterException("Twitter Error: Unknown (1)")
        except:
            self._deferred.errback(Failure())
    

    def _errback(self, failure):
        log.msg("_TwitterUpdater: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _TwitterException(Exception):

    def __init__(self, message=None):
        Exception.__init__(self, message)
