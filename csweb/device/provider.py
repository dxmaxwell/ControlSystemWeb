# coding=UTF-8
'''
Interface that define the standard operations for interacting with devices.
'''


class DeviceProvider():
    '''
    Abstract implementation of the DeviceProvider interface. 
    '''

    def get(self):
        '''
        Override this abstract implementation to handle the GET operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive the value of the device or else the errback should be
        called with the appropriate failure or exception.
        '''
        raise NotImplementedError()


    def put(self, value):
        '''
        Override this abstract implementation to handle the PUT operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive the value sent to the device or else the errback should be
        called with the appropriate failure or exception.
        '''
        raise NotImplementedError()


    def subscribe(self, protocolFactory):
        '''
        Override this abstract implementation to handle the SUBSCRIBE operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive an instance of the Protocol built by the specified
        ProtocolFactory or else the errback should be called with the 
        appropriate failure or exception.
        '''
        raise NotImplementedError()


class DeviceFactory():
    '''
    Abstract implementation of the DeviceFactory interface. 
    '''

    def cacheable(self):
        '''
        Override this abstract implementation to indicate if this factory is cacheable.

        The implementation must resuturn True or False.
        '''
        raise NotImplementedError()


    def buildProvider(self, uri):
        '''
        Override this abstract implementation to build a "DeviceProvder" for the specified URI.

        The implementation must return a "DeviceProvider" object or raise a "ValueError" exception.
        '''
        raise NotImplementedError()


class NotSupportedError(ValueError):
    '''
    A custom exception class to indicate that the specified URI is not supported.

    For example the scheme of the URI may be different than expected by the factory.
    '''
    pass
