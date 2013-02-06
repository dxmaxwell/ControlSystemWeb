'''
Configure EPICS device provider.
'''

from csweb.epics.provider import EpicsDeviceProvider

epicsDeviceProvider = EpicsDeviceProvider();
deviceManager.addProvider(epicsDeviceProvider)
log.msg('epics.py: Add EpicsDeviceProvider: %(d)s', d=epicsDeviceProvider, logLevel=_INFO)
