# coding=UTF-8
'''
Send mail notifications on events.
'''

from StringIO import StringIO
from email.utils import parseaddr, formataddr
from email.mime.text import MIMEText

from .. import device

from ..util import log

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.mail.smtp import SMTPSenderFactory

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class MailNotifier:

    def __init__(self, smtpHost, fromAddr):
        
        if isinstance(smtpHost, (list, tuple)):
            if len(smtpHost) > 1:
                self._smtp = (smtpHost[0], smtpHost[1])
            elif len(smtpHost) > 0:
                self._smtp = (smtpHost[0], 25)
        else:
            self._smtp = (str(smtpHost), 25)
        
        self._from = parseaddr(fromAddr)
        if self._from[1] == '':
            log.msg("MailNotifier: __init__: Invalid 'from' email address. Sending mail my fail!", logLevel=_WARN)
        
        self._subscriptions = {}


    def register(self, url, dest):
        if url not in self._subscriptions:
            log.msg("MailNotifier: register: No subsciption for URL %(r)s", r=url, logLevel=_DEBUG)
            protocolFactory = MailNotifierSubscriptionProtocolFactory(url, self)
            deferred = device.subscribe(url, protocolFactory)
            subscription = _MailNotifierSubscription(deferred)
            log.msg("MailNotifier: register: Add subsciption %(s)s", s=subscription, logLevel=_TRACE)
            self._subscriptions[url] = subscription
        else:
            log.msg("MailNotifier: register: Subsciption found for URL %(r)s", r=url, logLevel=_DEBUG)
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

        log.msg("MailNotifier: notify: Message: %(m)s", m=msg, logLevel=_TRACE)

        for dest in destinations:
            log.msg("MailNotifier: notify: Send to %(d)s", d=dest, logLevel=_TRACE)
            mime = MIMEText(msg)
            mime['To'] = formataddr(dest)
            mime['From'] =  formataddr(self._from)
            mime['Subject'] = "%s Update" % data['pvname']

            smptDeferred = Deferred()
            smptDeferred.addCallback(self._notify_callback)
            smptDeferred.addErrback(self._notify_errback)

            senderFactory = SMTPSenderFactory(self._from[1], dest[1], StringIO(mime), smptDeferred)
            reactor.connectTCP(self._smtp[0], self._smtp[1], senderFactory)


    def _notify_callback(self, result):
        log.msg("MailNotifier: _notify_callback: Sending email successful %(r)s", r=result, logLevel=_TRACE)


    def _notify_errback(self, err):
        log.msg("MailNotifier: _notify_errback: Error while sending mail: %(e)s", e=err, logLevel=_WARN)



class _MailNotifierSubscription:

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
        log.msg("_MailNotifierSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
        self._protocol = protocol
        for dest in self._destinations:
            self._protocol.addDestination(dest)
        del self._destinations[:]
        
        
    def _subscribeErrback(self, failure):
        log.msg("_MailNotifierSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_DEBUG)



class MailNotifierSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier
        self._destinations = []


    def addDestination(self, dest):
        parsedest = parseaddr(dest)
        if parsedest[1] != '':
            self._destinations.append(parsedest)
        else:
            log.msg("MailNotifierSubscriptionProtocol: addDestination: Destination address parse error: %(a)s", a=dest, logLevel=_WARN)
        

    def dataReceived(self, data):
        log.msg("MailNotifierSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_DEBUG)
        self._notifier.notify(self._url, data, self._destinations)
        


class MailNotifierSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol Factory
    '''

    def __init__(self, url, notifier):
        self._url = url
        self._notifier = notifier


    def buildProtocol(self, addr):
        return MailNotifierSubscriptionProtocol(self._url, self._notifier)
