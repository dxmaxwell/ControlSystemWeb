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


def startLogging(*args, **kwargs):
	return log.startLogging(*args, **kwargs)


def msg(msg=None, **kwargs):    
    if msg is not None:
        kwargs['format'] = msg
    return log.msg(**kwargs)


def err(msg=None, **kwargs):
	if msg is not None:
		kwargs['format'] = msg
	return log.err(**kwargs)
