# coding=UTF-8
'''
Configure logging.
'''

from csweb.util import log

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN

log.startLogging(sys.stdout)
