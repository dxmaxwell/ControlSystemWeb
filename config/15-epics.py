'''
Configure EPICS device provider.
'''

from csweb.epics.provider import EpicsDeviceFactory

epicsDeviceFactory = EpicsDeviceFactory();
deviceManager.addFactory(epicsDeviceFactory)
log.msg('epics.py: Add EpicsDeviceFactory: %(d)s', d=epicsDeviceFactory, logLevel=_INFO)
