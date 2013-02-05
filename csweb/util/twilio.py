# coding=UTF-8
'''
A Twisted enabled Twilio utility.

(This could eventually become a separate library.)
'''

try:
    from cStringIO import StringIO
except:
    from  StringIO import StringIO

import urllib, base64

from ..util import log, json

from twisted.web.http_headers import Headers
from twisted.web.client import FileBodyProducer, ResponseDone, Agent
from twisted.internet import defer, reactor, protocol
from twisted.python.failure import Failure

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


TWILIO_BASE_URL = 'https://api.twilio.com/2010-04-01'


class Twilio:

    def __init__(self, accountSid, accountTok, fromNumber=None):
        self._accountSid = accountSid
        self._accountTok = accountTok
        self._fromNumber = fromNumber

        self._agent = Agent(reactor)


    def sendSMS(self, toNumber, message, fromNumber=None):
        deferred = defer.Deferred();

        try:
            if fromNumber is None:
                if self._fromNumber is not None:
                    fromNumber = self._fromNumber
                else:
                    emsg = 'No "From" number specified, unable to send SMS.'
                    log.msg('Twilio: sendSMS: %(m)s', m=emsg, logLevel=_WARN)    
                    raise _TwilioException(emsg)
        except:
            reactor.callLater(0, deferred.errback, Failure())
            return deferred
        
        if len(message) > 160:
            message = message[:160]
            log.msg('Twilio: sendSMS: Message length >160 characters, will truncate message.', logLevel=_WARN)

        parameters = { 'From':fromNumber, 'To':toNumber, 'Body':message }
        http_url = '%s/Accounts/%s/SMS/Messages.json' % (TWILIO_BASE_URL, self._accountSid)

        log.msg("Twilio: sendSMS: Message: %(s)s", s=message, logLevel=_TRACE)
        request = _TwilioRequest(http_method='POST', http_url=http_url, parameters=parameters, accountTok=self._accountTok, accountSid=self._accountSid)

        _TwilioSendSMS(deferred, self._agent, request)
        return deferred


class _TwilioSendSMS:

    def __init__(self, deferred, agent, request):
        self._deferred = deferred
        
        headers = Headers()
        for k, v in request.to_header().items(): headers.addRawHeader(k, v)

        body = FileBodyProducer(StringIO(request.to_postdata()))

        d = agent.request(request.method, request.url, headers, body)
        d.addCallback(self._callback)
        d.addErrback(self._errback)


    def _callback(self, response):
        log.msg("_TwilioSendSMS: _callback: Response received", logLevel=_TRACE)
        response.deliverBody(_TwilioResponseProtocol(self._deferred))
    

    def _errback(self, failure):
        log.msg("_TwilioSendSMS: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _TwilioRequest:

    def __init__(self, http_url='', http_method='GET', parameters={}, accountTok='', accountSid=''):
        self.url = http_url
        self.method = http_method
        self._parameters = parameters
        self._accountSid = accountSid
        self._accountTok = accountTok


    def to_postdata(self):
        return urllib.urlencode(self._parameters)


    def to_header(self):
        header =  { 'Content-Type':'application/x-www-form-urlencoded' }
        authorization = '%s:%s' % (self._accountSid, self._accountTok)
        header['Authorization'] = 'Basic ' + base64.b64encode(authorization)
        return header


class _TwilioException(Exception):

    def __init__(self, message=None):
        Exception.__init__(self, message)


class _TwilioResponseProtocol(protocol.Protocol):

    def __init__(self, deferred):
        self._deferred = deferred
        self._data = StringIO()


    def connectionMade(self):
        log.msg("_TwilioResponseProtocol: connectionMade: Log Connection Made", logLevel=_TRACE)


    def dataReceived(self, data):
        log.msg("_TwilioResponseProtocol: dataReceived: Data type: %(t)s", t=type(data), logLevel=_TRACE)
        self._data.write(data)


    def connectionLost(self, reason):
        if isinstance(reason.value, ResponseDone):   
            log.msg("_TwilioResponseProtocol: connectionLost: Reason: %(r)s", t=reason, logLevel=_TRACE)
            try:
                data = json.parse(self._data.getvalue())
            except:
                log.msg("_TwilioResponseProtocol: connectionLost: Error parsing JSON.", logLevel=_WARN)
                self._deferred.errback();
                return

            self._deferred.callback(data)

        else:
            log.msg("_TwilioResponseProtocol: connectionLost: Reason: %(r)s", t=reason, logLevel=_WARN)
            self._deferred.errback(reason)
