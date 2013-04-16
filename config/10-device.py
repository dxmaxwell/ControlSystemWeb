# coding=UTF-8
'''
Initialize Device Manager.
'''

from csweb import device

deviceManager = device.manager
log.msg('device.py: DeviceManager: %(d)s', d=deviceManager, logLevel=_INFO)
