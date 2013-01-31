# coding=UTF-8
'''
Initialize Device Manager.
'''

from csweb import device

deviceManager = device.instance()
log.msg('device.py: DeviceManager: %(d)s', d=deviceManager, logLevel=_TRACE)
