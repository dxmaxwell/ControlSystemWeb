# coding=UTF-8
'''
Send twitter notifications on events.
'''

from .. import device

from ..util import log
from ..util.twitter import TwitterAgent

from .notifier import Notifier

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.defer import Deferred


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class TwitterNotifier(Notifier):

    def __init__(self, twitterAgents={}):
        Notifier.__init__(self)
        self._agents = {}
        if isinstance(twitterAgents, dict):
            for n, a in twitterAgents.items():
                self.addAgent(n, a)


    def addAgent(self, name, agent):
        if isinstance(agent, TwitterAgent):
            if name not in self._agents:
                log.msg("TwitterNotifier: notify: addAgent: New Agent: %(n)s", n=name, logLevel=_TRACE)
            else:
                log.msg("TwitterNotifier: notify: addAgent: Replace Agent: %(n)s", n=name, logLevel=_DEBUG)
            self._agents[name] = agent
        else:
            log.msg("TwitterNotifier: notify: addAgent: Agent is Unexpected Class: %(n)s", n=name, logLevel=_WARN)


    def notify(self, url, data, destinations):

        msg = self._toHashTag(data['pvname']) + " "
        if 'char_value' in data:
            msg += data['char_value'] 
        elif 'value' in data:
            msg += str(data['value'])
        else:
            msg += "(UNKNOWN)"

        log.msg("TwitterNotifier: notify: Message: %(m)s", m=msg, logLevel=_DEBUG)

        for dest in destinations:
            if dest in self._agents:
                log.msg("TwitterNotifier: notify: Destination Found: %(d)s", d=dest, logLevel=_DEBUG)
                d = self._agents[dest].update(msg)
                d.addCallback(self._notifyCallback)
                d.addErrback(self._notifyErrback)
            else:
                log.msg("TwitterNotifier: notify: Destination NOT Found: %(d)s", d=dest, logLevel=_WARN)


    def _toHashTag(self, s):
        return '#' + s.replace(':', '')
