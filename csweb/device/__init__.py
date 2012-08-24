# coding=UTF-8
'''
Convenience methods to install and use the DeviceManager singleton. 
'''

from .manager import DeviceManager 

from .provider import DeviceProvider


_instance = None


def install(deviceManager=None):
    '''
    Install the specified DeviceManager or the default if none is specified.
    '''
    global _instance
    if isinstance(deviceManager, DeviceProvider): 
        _instance = deviceManager
    elif deviceManager == None:
        _instance = DeviceManager()
    else:
        raise TypeError("DeviceManager is not an instance of DeviceProvider")
    return _instance


def instance():
    '''
    Get DeviceManager instance, install default DeviceManager if required.
    '''
    if _instance == None:
        return install()
    else:
        return _instance


def get(*args, **kwargs):
    '''
    Delegate "get" to DeviceManager instance.
    '''
    return instance().get(*args, **kwargs)
    

def put(*args, **kwargs):
    '''
    Delegate "put" to DeviceManager instance.
    '''
    return instance().put(*args, **kwargs)


def subscribe(*args, **kwargs):
    '''
    Delegate "subscribe" to DeviceManager instance.
    '''
    return instance().subscribe(*args, **kwargs)


def supports(*args, **kwargs):
    '''
    Delegate "supports" to DeviceManager instance.
    '''
    return instance().supports(*args, **kwargs)
