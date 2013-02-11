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


class TwilioSMSAgent:

    def __init__(self, httpAgent):
        self._httpAgent = httpAgent


    def send(self, toNumber, fromNumber, message):
        deferred = defer.Deferred();
        
        try:
            if toNumber is None:
                log.msg("TwilioSMSAgent: send: No 'To' number specified, unable to send SMS.'", logLevel=_WARN)
                raise _TwilioException("No 'To' number specified.")
        
            if fromNumber is None:
                log.msg("TwilioSMSAgent: send: No 'From' number specified, unable to send SMS.'", logLevel=_WARN)    
                raise _TwilioException("No 'From' number specified.")
        except:
            reactor.callLater(0, deferred.errback, Failure())
            return deferred
        
        if len(message) > 160:
            message = message[:160]
            log.msg('TwilioSMSAgent: send: Message length >160 characters, will truncate message.', logLevel=_WARN)

        log.msg("TwilioSMSAgent: send: Message: %(s)s", s=message, logLevel=_TRACE)

        parameters = { 'To':toNumber, 'From':fromNumber, 'Body':message }
        _TwilioSMSAgentSender(deferred, self._httpAgent, parameters)
        return deferred


class _TwilioSMSAgentSender:

    def __init__(self, deferred, httpAgent, parameters):
        self._deferred = deferred
        url = "%s/Accounts/%s/SMS/Messages.json" % (TWILIO_BASE_URL, httpAgent.username)
        d = httpAgent.request('POST', url, body=parameters)
        d.addCallback(self._callback)
        d.addErrback(self._errback)


    def _callback(self, response):
        log.msg("_TwilioSMSAgentSender: _callback: Response received", logLevel=_TRACE)
        # Assume response is JSON, without checking the headers!
        try:
            body = json.parse(response.body)
        except:
            self._deferred.errback(Failure())

        try:
            if response.isSuccessful():
                self._deferred.callback(body)
            elif "message" in body:
                raise _TwilioException("Twilio Error: Message: " + body["message"])
            elif "code" in body:
                raise _TwilioException("Twilio Error: Code: " + body["code"])
            else:
                raise _TwilioResponseError("Twilio Error: Unknown")
        except:
            self._deferred.errback(Failure())
            

    def _errback(self, failure):
        log.msg("_TwilioSMSAgentSender: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _TwilioException(Exception):

    def __init__(self, message=None):
        Exception.__init__(self, message)
