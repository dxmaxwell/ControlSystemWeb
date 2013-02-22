# coding=UTF-8
'''
Send mail notifications on events.
'''

from email.utils import parseaddr, formataddr

from ..util import log
from .notifier import Notifier

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class MailNotifier(Notifier):

    def __init__(self, smtpAgent, fromAddress):
        Notifier.__init__(self)
        self._smtpAgent = smtpAgent
        fromAddress = parseaddr(fromAddress)
        if fromAddress[1] == '':
            log.msg("MailNotifier: __init__: Invalid 'From' address. Sending mail will fail!", logLevel=_WARN)
        self._fromAddress = formataddr(fromAddress)
        self._subscriptions = {}


    def notify(self, url, data, destinations):
        name = self._name_from_data(data)
        subject = "[CSWEB] " + name + " Update"
        message = name + ": " + self._str_value_from_data(data)
        log.msg("MailNotifier: notify: Message: %(m)s", m=message, logLevel=_DEBUG)

        for dest in destinations:
            log.msg("MailNotifier: notify: Send to %(d)s", d=dest, logLevel=_DEBUG)
            d = self._smtpAgent.send(dest, self._fromAddress, message, subject)
            d.addCallback(self._notifyCallback)
            d.addErrback(self._notifyErrback)
