# coding=UTF-8
'''
Utility for using the Twisted HTTP Agent.
'''

try:
    from cStringIO import StringIO
except:
    from  StringIO import StringIO

import base64, urllib

import oauth2 as oauth

from ..util import log

from twisted.web.http_headers import Headers
from twisted.web.client import FileBodyProducer, ResponseDone, Agent
from twisted.internet import defer, reactor, protocol
from twisted.python.failure import Failure


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class HTTPAgent():

    def __init__(self):
        self._urlencoded = False


    def request(self, method, uri, headers=None, body=None):
        log.msg("HTTPAgent: request: Headers:'%(h)s' Body:'%(b)s'", h=headers, b=body, logLevel=_TRACE)
        d = defer.Deferred()
        twBody = self._prepareBody(method, uri, headers, body)
        twHeaders = self._prepareHeaders(method, uri, headers, body)
        _HTTPAgentRequester(d, method, uri, twHeaders, twBody)
        return d


    def _prepareBody(self, method, uri, headers, body):
        twBody = None
        if isinstance(body, dict):
            self._urlencoded = True
            twBody = FileBodyProducer(StringIO(urllib.urlencode(body)))
        elif isinstance(body, basestring):
            twBody = FileBodyProducer(StringIO(body))
        elif body is not None:
            twBody = FileBodyProducer(body)
        return twBody


    def _prepareHeaders(self, method, uri, headers, body):
        twHeaders = None
        if isinstance(headers, Headers):
            twHeaders = headers
        elif isinstance(headers, dict):
            twHeaders = Headers()
            for k, v in headers.items():
                twHeaders.addRawHeader(k, v)
        if self._urlencoded:
            if twHeaders is None:
                twHeaders = Headers()
            twHeaders.addRawHeader("Content-Type", "application/x-www-form-urlencoded")
        return twHeaders
        

class BasicHTTPAgent(HTTPAgent):
    
    def __init__(self, username, password):
        HTTPAgent.__init__(self)
        self.username = username
        self._authication = 'Basic '+base64.b64encode(username+':'+password)


    def _prepareHeaders(self, method, uri, headers, body):
        twHeaders = HTTPAgent._prepareHeaders(self, method, uri, headers, body)
        if twHeaders is None:
            twHeaders = Headers()
        twHeaders.addRawHeader('Authorization',  self._authication)
        return twHeaders


class OAuthHTTPAgent(HTTPAgent):

    def __init__(self, consumer, token, oauthSigMethod=oauth.SignatureMethod_HMAC_SHA1()):
        HTTPAgent.__init__(self)
        self._oauthSigMethod = oauthSigMethod
        self._consumer = consumer
        self._token = token
        self._oauth_request = None


    def _prepareBody(self, method, uri, headers, body):
        twBody = None
        if isinstance(body, dict):
            self._oauth_request = oauth.Request.from_consumer_and_token(self._consumer, token=self._token, http_method=method, http_url=uri, parameters=body)
            self._oauth_request.sign_request(self._oauthSigMethod, self._consumer, self._token);
            twBody = FileBodyProducer(StringIO(self._oauth_request.to_postdata()))
        else:
            twBody = HTTPAgent._prepareBody(self, method, uri, headers, body)
        return twBody


    def _prepareHeaders(self, method, uri, headers, body):
        twHeaders = None
        if self._oauth_request is not None:
            self._urlencoded = True
            twHeaders = HTTPAgent._prepareHeaders(self, method, uri, headers, body)
            if twHeaders is None:
                twHeaders = Headers()
            for k, v in self._oauth_request.to_header().items():
                # The Twisted HTTP Agent has a problem with Unicode header keys and values,
                # which the OAuth2 library generates, so convert the header keys and values
                # to a regular strings from Unicode. (Possible corruption of the headers?)
                twHeaders.addRawHeader(str(k), str(v))
        else:
            twHeaders = HTTPAgent._prepareHeaders(self, method, uri, headers, body)
        return twHeaders


class _HTTPAgentRequester():

    _agent = Agent(reactor)

    def __init__(self, deferred, method, uri, headers=None, body=None):
        self._deferred = deferred
        d = self._agent.request(method, uri, headers, body)
        d.addCallback(self._callback)
        d.addErrback(self._errback)


    def _callback(self, response):
        log.msg("_HTTPAgentRequester: _callback: Response Received", logLevel=_TRACE)
        response.deliverBody(_HTTPAgentResponseProtocol(self._deferred, _HTTPAgentResponse(response)))
    

    def _errback(self, failure):
        log.msg("_HTTPAgentRequester: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _HTTPAgentResponse:

    def __init__(self, response):
        self.body = None
        self.code = response.code
        self.phrase = response.phrase
        self.version = response.version
        self.headers = {}
        for k, v in response.headers.getAllRawHeaders():
            self.headers[k] = v

    def __str__(self):
        buf = StringIO()
        buf.write("Response(")
        buf.write(" Version:")
        buf.write(str(self.version[0]))
        buf.write("/")
        buf.write(str(self.version[1]))
        buf.write(".")
        buf.write(str(self.version[2]))
        buf.write(" Code:")
        buf.write(str(self.code))
        buf.write(" (")
        buf.write(str(self.phrase))
        buf.write(")")
        buf.write(" Headers:")
        buf.write(str(self.headers))
        buf.write(" )")
        return buf.getvalue()

    def isInformational(self):
        return (self.code >= 100) and (self.code < 200)

    def isSuccessful(self):
        return (self.code >= 200) and (self.code < 300)

    def isRedirection(self):
        return (self.code >= 300) and (self.code < 400)

    def isClientError(self):
        return (self.code >= 400) and (self.code < 500)

    def isServerError(self):
        return (self.code >= 500) and (self.code < 600)


class _HTTPAgentResponseProtocol(protocol.Protocol):

    def __init__(self, deferred, response):
        self._deferred = deferred
        self._response = response
        self._data = StringIO()


    def connectionMade(self):
        log.msg("_HTTPAgentResponseProtocol: connectionMade: Log Connection Made", logLevel=_TRACE)


    def dataReceived(self, data):
        log.msg("_HTTPAgentResponseProtocol: dataReceived: Data type: %(t)s", t=type(data), logLevel=_TRACE)
        self._data.write(data)


    def connectionLost(self, reason):
        if isinstance(reason.value, ResponseDone):   
            log.msg("_HTTPAgentResponseProtocol: connectionLost: Reason: %(r)s", r=reason, logLevel=_TRACE)
            self._response.body = self._data.getvalue()
            self._deferred.callback(self._response)
        else:
            log.msg("_HTTPAgentResponseProtocol: connectionLost: Reason: %(r)s", r=reason, logLevel=_WARN)
            self._deferred.errback(reason)
