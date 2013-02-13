# coding=UTF-8
'''
Send SMS notifications on events.
'''

from .. import device

from ..util import log
from .notifier import Notifier


from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class SMSNotifier(Notifier):

    def __init__(self, smsAgent, fromNumber):
        Notifier.__init__(self)
        self._smsAgent = smsAgent
        self._fromNumber = fromNumber


    def notify(self, url, data, destinations):

        msg = data['pvname'] + ": "
        if 'char_value' in data:
            msg += data['char_value'] 
        elif 'value' in data:
            msg += str(data['value'])
        else:
            msg += "(UNKNOWN)"

        log.msg("SMSNotifier: notify: Message: '%(m)s'", m=msg, logLevel=_DEBUG)

        for dest in destinations:
            log.msg("SMSNotifier: notify: Destination: %(d)s", d=dest, logLevel=_DEBUG)
            smsDeferred = self._smsAgent.send(dest, self._fromNumber, msg)
            smsDeferred.addCallback(self._notifyCallback)
            smsDeferred.addErrback(self._notifyErrback)
