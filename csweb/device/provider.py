# coding=UTF-8
'''
DeviceProvider interface defines the standard operations for interacting with devices.
'''


class DeviceProvider():
    '''
    Abstract implementation of the DeviceProvider interface. 
    '''

    def get(self, uri):
        '''
        Override this abstract implementation to handle the GET operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive the value of the device or else the errback should be
        called with the appropriate failure or exception.
        '''
        raise NotImplementedError()


    def put(self, uri, value):
        '''
        Override this abstract implementation to handle the PUT operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive the value sent to the device or else the errback should be
        called with the appropriate failure or exception.
        '''
        raise NotImplementedError()


    def subscribe(self, uri, protocolFactory):
        '''
        Override this abstract implementation to handle the SUBSCRIBE operation.
        
        The implementation must return a "Deferred" object and the callback
        should receive an instance of the Protocol built by the specified
        ProtocolFactory or else the errback should be called with the 
        appropriate failure or exception.
        '''
        raise NotImplementedError()


    def supports(self, uri):
        '''
        Override this abstract implementation to indicate if the specified URI is supported.
        
        The implementation must return either True or False.
        '''
        return False
