# coding=UTF-8
'''
Convenience wrappers around the Twisted 'log' utility.
'''

import logging

from twisted.python import log

NOTSET   = logging.NOTSET   #  0
TRACE    = 5
DEBUG    = logging.DEBUG    # 10
INFO     = logging.INFO     # 20
WARN     = logging.WARN     # 30
ERROR    = logging.ERROR    # 40
FATAL    = logging.FATAL    # 50

_LEVEL = NOTSET


def startLogging(*args, **kwargs):
    log.startLogging(*args, **kwargs)


def getLevel():
    return _LEVEL


def setLevel(level):
    global _LEVEL
    _LEVEL = level


def msg(msg=None, **kwargs):
    global _LEVEL
    if 'logLevel' not in kwargs:
        kwargs['logLevel'] = NOTSET
    if kwargs['logLevel'] >= _LEVEL:
        if msg is not None:
            kwargs['format'] = msg
        log.msg(**kwargs)


def err(msg=None, **kwargs):
    global _LEVEL
    if 'logLevel' not in kwargs:
        kwargs['logLevel'] = NOTSET
    if kwargs['logLevel'] >= _LEVEL:
        if msg is not None:
            kwargs['format'] = msg
        log.err(**kwargs)
