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

        msg = data['pvname'] + ": "
        if 'char_value' in data:
            msg += data['char_value'] 
        elif 'value' in data:
            msg += str(data['value'])
        else:
            msg += "(UNKNOWN)"

        log.msg("MailNotifier: notify: Message: %(m)s", m=msg, logLevel=_DEBUG)

        for dest in destinations:
            log.msg("MailNotifier: notify: Send to %(d)s", d=dest, logLevel=_DEBUG)
            smptDeferred = self._smtpAgent.send(dest, self._fromAddress, msg, "%s Update" % data['pvname'])
            smptDeferred.addCallback(self._notifyCallback)
            smptDeferred.addErrback(self._notifyErrback)
