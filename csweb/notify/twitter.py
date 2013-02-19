# coding=UTF-8
'''
Send twitter notifications on events.
'''

import re, datetime

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

    def __init__(self, twitterAgents={}, prefix="", postfix=""):
        Notifier.__init__(self)
        self._prefix = prefix
        self._postfix = postfix
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

        if "name" in data:
            msg = self._toHashTag(data["name"])            
        elif "pvname" in data:
            msg = self._toHashTag(data["pvname"])
        else:
            msg = "UnknownDevice"

        if "char_value" in data:
            msg += " " + data['char_value']
            if "units" in data:
                msg += data["units"]
        elif "value" in data:
            msg += " " + str(data["value"])
            if "units" in data:
                msg += data["units"]
        else:
            msg += " N/A"

        if "timestamp" in data:
            time = datetime.datetime.fromtimestamp(data["timestamp"])
        else:
            time = datetime.datetime.today()

        prefix = time.strftime(self._prefix)
        postfix = time.strftime(self._postfix)
        
        length = 160 - len(prefix) - len(postfix)
        if length <= 0:
            log.msg("TwitterNotifier: notify: Prefix and Postfix length >160, will truncate", logLevel=_WARN)
            if len(prefix) > 40:
                prefix = prefix[:37] + "..."
            if len(postfix) > 40:
                postfix = postfix[:37] + "..."
            length = 160 - len(prefix) - len(postfix)

        if length < len(msg):
            log.msg("TwitterNotifier: notify: Message length >160 characters, will truncate", logLevel=_DEBUG)
            msg = msg[:(length-3)] + "..."

        msg = prefix + msg + postfix
        
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
        return '#' + re.sub(r"[^a-zA-Z0-9]", "", s)
