# coding=UTF-8
'''
Utilities for configuring notifiers.
'''

import re, os.path, datetime, time, ConfigParser

from ..util import log

from twisted.python import filepath
from twisted.internet import task, threads

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_INFO = log.INFO
_WARN = log.WARN


class GeneralFileConfig:

    def __init__(self, path, notifiers={}, interval=10):
        self._path = path
        self._notifiers = notifiers
        self._configTime = 0
        self._configLock = False
        self._interval = interval
        self._loopingCall = task.LoopingCall(self._configure)
        self._loopingCall.start(interval)


    def addNotifier(self, name, notifier):
        self._notifiers[name] = notifier


    def removeNotifier(self, name):
        if name in self._notifiers:
            del self._notifiers[name]


    def _configure(self):

        if self._configLock:
            log.msg("GeneralFileConfig: _configure: Configuration process already started. (Interval:%(i)ds)", i=self._interval, logLevel=_WARN)
            return

        self._configLock = True

        configPath = filepath.FilePath(self._path)

        if not configPath.isfile():
            log.msg("GeneralFileConfig: _configure: Configuration path is not a regular file: %(p)s", p=configPath, logLevel=_WARN)
            self._configLock = False
            return

        if configPath.getModificationTime() < self._configTime:
            log.msg("GeneralFileConfig: _configure: Configuration file has not been modified since last update.", logLevel=_TRACE)
            self._configLock = False
            return

        log.msg("GeneralFileConfig: _configure: Configuration file has been modified.  Update notifier configuration.", logLevel=_INFO)
        d = threads.deferToThread(self._configure_thread, self._path, self._notifiers.keys())
        d.addCallback(self._configure_thread_callback)
        d.addErrback(self._configure_thread_errback)


    @staticmethod
    def _configure_thread(path, notifiers):
        
        configParser = ConfigParser.SafeConfigParser()
        with open(path, 'r') as configFile:
            configParser.readfp(configFile)

        config = {}
        variables = {}

        for section in configParser.sections():
            url = section.strip()
            if len(url) == 0:
                continue
            for option, value in configParser.items(section):
                notifier = option.strip()
                if len(notifier) == 0:
                    continue
                if notifier not in notifiers:
                    continue
                if notifier not in config:
                    config[notifier] = {}
                if url not in config[notifier]:
                    config[notifier][url] = {}
                for dest in value.strip().split(','):
                    m = re.match(r"\s*(.*)\s*\((.*)\)\s*", dest)
                    if m:
                        dest = m.group(1)
                        expiry = m.group(2)
                    else:
                        expiry = datetime.datetime.max
                    dest = dest.strip()
                    if len(dest) == 0:
                        continue
                    config[notifier][url][dest] = expiry

        return config


    def _configure_thread_callback(self, configuration):
        log.msg("GeneralFileConfig: _configure_thread_callback: Configuration: %(c)s", c=configuration, logLevel=_DEBUG)
        
        for name, notifier in self._notifiers.iteritems():

            if name in configuration:
                log.msg("GeneralFileConfig: _configure_thread_callback: Configuring notifier: '%(n)s'", n=name, logLevel=_DEBUG)
                configured = configuration[name]
            else:
                log.msg("GeneralFileConfig: _configure_thread_callback: No Configuration for notifier: '%(n)s'", n=name, logLevel=_DEBUG)
                configured = {}

            registered = notifier.registered()
            registeredURLs = set(registered.iterkeys())
            configuredURLs = set(configured.iterkeys())

            for url in configuredURLs.difference(registeredURLs):
                for dest, expiry in configured[url].iteritems():
                    notifier.register(url, dest, expiry)

            for url in registeredURLs.difference(configuredURLs):
                for dest in registered[url].iterkeys():
                    notifier.unregister(url, dest)

            for url in registeredURLs.intersection(configuredURLs):
                # (Re)register all configured destinations,
                # just in case the expiry date has changed.
                for dest, expiry in configured[url].iteritems():
                    notifier.register(url, dest, expiry)
                # Now unregister only the destinations that
                # have not been specified in the configuration.
                registeredDests = set(registered[url].iterkeys())
                configuredDests = set(configured[url].iterkeys())
                for dest in registeredDests.difference(configuredDests):
                    notifier.unregister(url, dest)

        self._configTime = time.time()
        self._configLock = False


    def _configure_thread_errback(self, failure):
        log.msg("GeneralFileConfig: _configure_thread_errback: Failure: %(f)s", f=failure, logLevel=_WARN)
        self._configLock = False
