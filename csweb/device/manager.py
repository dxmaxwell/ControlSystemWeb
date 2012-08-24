# coding=UTF-8
'''
DeviceManager is a special DeviceProvider that delegates to other DeviceProviders.
'''


from twisted.internet import defer, reactor

from ..util import log

from .provider import DeviceProvider


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class NotSupportedError(Exception):
    '''
    Simple exception to indicate no DeviceProvder supports the given URI.
    '''
    pass


class DeviceManager(DeviceProvider):
    '''
    A simple DeviceProvider that delegates to a list of DeviceProviders.
    '''
    
    def __init__(self, deviceProviders=None):
        '''
        Initialize with an optional list of DeviceProviders.
        '''
        self._providers = []
        if deviceProviders != None:
            self.addProvider(deviceProviders)


    def addProvider(self, deviceProvider):
        '''
        Add the given DeviceProvider (or list of DeviceProviders) to the list of delegates.
        '''
        if isinstance(deviceProvider, (list, tuple)):
            log.msg('DeviceManager: addProvider: Given list or tuple of DeviceProviders', logLevel=_TRACE)
            for provider in deviceProvider:
                self._addProvider(provider)
        else:
            self._addProvider(deviceProvider)


    def _addProvider(self, deviceProvider):
        '''
        Actually append the DeviceProvider to the list of delegates.
        '''
        if isinstance(deviceProvider, DeviceProvider):
            if deviceProvider not in self._providers:
                log.msg('DeviceManager: _addProvider: Append DeviceProvider: %(d)s', d=deviceProvider, logLevel=_DEBUG)
                self._providers.append(deviceProvider)
            else:
                log.msg('DeviceManager: _addProvider: DeviceProvider already added: %(d)s', d=deviceProvider, logLevel=_DEBUG)
        else:
            log.msg('DeviceManager: _addProvider: DeviceProvider incorrect class: %(d)s', d=deviceProvider, logLevel=_WARN)


    def removeProvider(self, deviceProvider):
        '''
        Remove the given provider from the list of DeviceProviders.
        '''
        if deviceProvider in self._providers:
            log.msg('DeviceManager: removeProvider: Remove DeviceProvider: %(d)s', d=deviceProvider, logLevel=_DEBUG)
            self._providers.remove(deviceProvider)
        else:
            log.msg('DeviceManager: removeProvider: DeviceProvider not added: %(d)s', d=deviceProvider, logLevel=_WARN)
   
   
    def subscribe(self, uri, protocolFactory):
        '''
        Delegate method to available DeviceProviders. 
        '''
        notSupported = True
        for provider in self._providers:
            if provider.supports(uri):
                notSupported = False
                try:
                    log.msg('DeviceManager: subscribe: Found supporting DeviceProvider: %(d)s', d=provider, logLevel=_DEBUG)
                    return provider.subscribe(uri, protocolFactory)
                except NotImplementedError:
                    log.msg('DeviceManager: subscribe: Found DeviceProvider but does not implement "subscribe": %(d)s', d=provider, logLevel=_WARN)
                    continue
                except Exception as e:
                    log.msg('DeviceManager: subscribe: Found DeviceProvider but "subscribe" raised exception: %(d)s', d=e, logLevel=_WARN)
                    return self._callErrbackLater(e)
                
        if notSupported:
            return self._callErrbackLater(NotSupportedError())    
        else:       
            return self._callErrbackLater(NotImplementedError())
    
    
    def supports(self, uri):
        '''
        Delegate method to available DeviceProviders.
        '''
        for provider in self._providers:
            try:
                if provider.supports(uri):
                    log.msg('DeviceManager: supports: URI supported by DeviceProvider: %(d)s', d=provider, logLevel=_DEBUG)
                    return True
            except:
                log.msg('DeviceManager: supports: DeviceProvider raised exception, will ignore: %(d)s', d=provider, logLevel=_WARN)
                continue
        
        return False


    def _callErrbackLater(self, fail=None):
        '''
        Create a deferred and schedule its errback method to be called ASAP. 
        '''
        d = defer.Deferred()
        reactor.callLater(0, d.errback, fail)
        return d
