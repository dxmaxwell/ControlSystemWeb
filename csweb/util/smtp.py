# coding=UTF-8
'''
Utility for using the Twisted SMTP Factory.
'''

try:
    from cStringIO import StringIO
except:
    from  StringIO import StringIO

from email.message import Message
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

from ..util import log

from twisted.internet import defer, reactor
from twisted.mail.smtp import SMTPSenderFactory

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class SMTPAgent:

    def __init__(self, host, port=25):
        if isinstance(host, (list, tuple)):
            if len(host) > 1:
                self._host = (str(host[0]), int(host[1]))
            elif len(host) > 0:
                self._host = (str(host[0]), int(port))
        else:
            self._host = (str(host), int(port))


    def send(self, toAddress, fromAddress, message, subject="(No Subject)", ccAddress=None, bccAddress=None):
        deferred = defer.Deferred()

        fromAddress = self._parse_address(fromAddress)
        if len(fromAddress) == 0:
            log.msg("SMTPAgent: send: No 'From' address specified, unable to send mail.", logLevel=_WARN)
            try:
                raise _SMTPException("No 'From' address specified")
            except:
                reactor.callLater(0, deferred.errback, Failure())
                return deferred

        if len(fromAddress) >  1:
            log.msg("SMTPAgent: send: Multiple 'From' addresses specified, using using: %(a)s", a=fromAddress[0], logLevel=_DEBUG)
        smtpFromAddress = fromAddress[0][1]

        toAddress = self._parse_address(toAddress)
        ccAddress = self._parse_address(ccAddress)
        bccAddress = self._parse_address(bccAddress)

        smtpToAddresses = []
        for addr in toAddress:
            smtpToAddresses.append(addr[1])
        for addr in ccAddress:
            smtpToAddresses.append(addr[1])
        for addr in bccAddress:
            smtpToAddresses.append(addr[1])

        if len(smtpToAddresses) == 0:
            log.msg("SMTPAgent: send: No destination address specified, unable to send mail.", logLevel=_WARN)
            try:
                raise _SMTPException("No 'To' address specified")
            except:
                reactor.callLater(0, deferred.errback, Failure())
                return deferred

        if isinstance(message, Message):
            mime = message
        else:
            mime = MIMEText(str(message))
            mime['Subject'] = str(subject)
            mime['From'] = self._join_address(fromAddress)
            mime['To'] = self._join_address(toAddress)
            mime['Cc'] = self._join_address(ccAddress)

        _SMTPAgentSender(self._host, smtpFromAddress, smtpToAddresses, StringIO(mime.as_string()), deferred)
        return deferred


    def _parse_address(self, address):
        addresses = []
        if isinstance(address, basestring):
            addr = parseaddr(address)
            if address[1] != "":
                addresses.append(addr)
        elif isinstance(address, (list,tuple)):
            for addr in address:
                addresses.extend(self._parse_address(addr))
        return addresses


    def _join_address(self, address):
        sep = False
        buf = StringIO();
        for addr in address:
            if sep:
                buf.write(",")
            else:
                sep = True
            buf.write(formataddr(addr))
        return buf.getvalue()


class _SMTPAgentSender:

    def __init__(self, host, fromAddress, toAddress, message, deferred):
        self._deferred = deferred
        d = defer.Deferred()
        d.addCallback(self._callback)
        d.addErrback(self._errback)
        senderFactory = SMTPSenderFactory(fromAddress, toAddress, message, d)
        reactor.connectTCP(host[0], host[1], senderFactory)


    def _callback(self, result):
        log.msg("_SMTPAgentSender: _callback: Success: %(r)s", r=result, logLevel=_TRACE)
        self._deferred.callback(result)


    def _errback(self, failure):
        log.msg("_SMTPAgentSender: _errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._deferred.errback(failure)


class _SMTPException(Exception):

    def __init__(self, message=None):
        Exception.__init__(self, message)
