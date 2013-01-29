# coding=UTF-8
'''
A Twisted enabled Twitter utility.

(This could eventually become a separate library.)
'''

import oauth2 as oauth

from StringIO import StringIO

from ..util import log, json

from twisted.web.http_headers import Headers
from twisted.web.client import FileBodyProducer, ResponseDone, Agent
from twisted.internet import defer, ssl, reactor, protocol


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


TWITTER_BASE_URL = 'https://api.twitter.com/1.1'


class Twitter:

    def __init__(self, consumer, token):
        self._consumer = consumer
        self._token = token

        self._agent = Agent(reactor)


    def update(self, status):
        deferred = defer.Deferred();
        parameters = { 'status':status }
        http_url = TWITTER_BASE_URL + '/statuses/update.json'

        log.msg("Twitter: update: Request status update: %(s)s", s=status, logLevel=_DEBUG)
        oauth_request = oauth.Request.from_consumer_and_token(self._consumer, token=self._token, http_method='POST', http_url=http_url, parameters=parameters)
        oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), self._consumer, self._token);
        
        _TwitterUpdate(deferred, self._agent, oauth_request)
        return deferred


class _TwitterUpdate:

    def __init__(self, deferred, agent, oauth_request):
        self._deferred = deferred
        
        headers = Headers({'Content-Type' : [ 'application/x-www-form-urlencoded' ]})
        for k, v in oauth_request.to_header().items(): headers.addRawHeader(k, v)

        body = FileBodyProducer(StringIO(oauth_request.to_postdata()))

        # oauth_request.url is unicode, it must be converted to regular string. #
        d = agent.request(oauth_request.method, str(oauth_request.url), headers, body)
        d.addCallback(self._callback)
        d.addErrback(self._errback)


    def _callback(self, response):
        log.msg("_TwitterUpdate: _callback: Response received", logLevel=_DEBUG)
        response.deliverBody(_TwitterResponseProtocol(self._deferred))
    

    def _errback(self, failure):
        log.msg("_TwitterUpdate: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _TwitterResponseProtocol(protocol.Protocol):

    def __init__(self, deferred):
        self._deferred = deferred
        self._data = StringIO()


    def connectionMade(self):
        log.msg("_TwitterResponseProtocol: connectionMade: Log Connection Made", logLevel=_DEBUG)
        pass


    def dataReceived(self, data):
        log.msg("_TwitterResponseProtocol: dataReceived: Data type: %(t)s", t=type(data), logLevel=_DEBUG)
        self._data.write(data)


    def connectionLost(self, reason):
        log.msg("_TwitterResponseProtocol: connectionLost: Reason: %(r)s", t=reason, logLevel=_DEBUG)
        if isinstance(reason.value, ResponseDone):   
            try:
                data = json.parse(self._data.getvalue())
                self._deferred.callback(data)
            except:
                self._deferred.errback();
        else:
            self._deferred.errback(reason)
