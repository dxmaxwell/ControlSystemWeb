# coding=UTF-8
'''
DeviceManager is a special DeviceFactory that delegates to other DeviceFactories.
'''

import time

from collections import OrderedDict

from ..util import log

from .provider import DeviceFactory, NotSupportedError


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class DeviceManager(DeviceFactory):
    '''
    Abstract implementation of the DeviceManager interface. 

    A "DeviceManager" simply implements the "DeviceFactory" interface. This may be extended in the future.
    '''
    pass


class DefaultDeviceManager(DeviceManager):
    '''
    A simple DeviceFactory that delegates to a list of DeviceFactory.
    '''
    
    def __init__(self, maxCacheSize=1000):
        '''
        Initialize with an optional DeviceFactory (or list of DeviceFactories).
        '''
        self._factories = []
        self._cacheable = True
        self._maxCacheSize = maxCacheSize
        self._provider_cache = OrderedDict()


    def addFactory(self, deviceFactory):
        '''
        Add the given "DeviceFactory" to the list of factories.
        '''
        if not isinstance(deviceFactory, DeviceFactory):
            log.msg('DeviceManager: addFactory: Object is not an instance of DeviceFacory: %(d)s', d=deviceFactory, logLevel=_WARN)
        elif deviceFactory in self._factories:
            log.msg('DeviceManager: addFactory: DeviceFactory already added to delegates: %(d)s', d=deviceFactory, logLevel=_DEBUG)
        else:
            log.msg('DeviceManager: addFactory: Append DeviceFactory to delegates: %(d)s', d=deviceFactory, logLevel=_TRACE)
            self._factories.append(deviceFactory)
            # Update the value of 'cacheable'.
            self._cacheable &= deviceFactory.cacheable()
            # Clearing the cache is not requried.
            #self._clear_provider_cache()


    def removeFactory(self, deviceFactory):
        '''
        Remove the given provider from the list of DeviceProviders.
        '''
        if deviceFactory not in self._factories:
            log.msg('DeviceManager: removeFactory: DeviceFactory not found in delegates: %(d)s', d=deviceFactory, logLevel=_WARN)
        else:
            log.msg('DeviceManager: removeFactory: Remove DeviceFactory from delegates: %(d)s', d=deviceFactory, logLevel=_TRACE)
            self._factories.remove(deviceFactory)
            # Update the value of 'cacheable'.
            self._cacheable = True
            for factory in self._factories:
                self._cacheable &= factory.cacheable()
            # Clear the cache. Entries could be invalid.
            self._clear_provider_cache()
   
   
    def cacheable(self):
        '''
        All delegates must be cacheable for this manager to be cacheable.
        '''
        return self._cacheable

    
    def buildProvider(self, uri):
        '''
        Delegate method to the available factories.
        '''
        start = time.clock()
        provider = self._pop_provider_cache(uri)
        if provider is not None:
            log.msg("DeviceManager: buildProvider: DeviceProvider found in cache (%(t)gs): %(p)s", t=(time.clock()-start), p=provider, logLevel=_TRACE)
            return provider
        for factory in self._factories:
            try:
                provider = factory.buildProvider(uri)
                if factory.cacheable():
                    self._push_provider_cache(uri, provider)
                    log.msg("DeviceManager: buildProvider: DeviceFactory built (%(t)gs) and cached: %(p)s", t=(time.clock()-start), p=provider, logLevel=_TRACE)
                else:
                    log.msg("DeviceManager: buildProvider: DeviceFactory built (%(t)gs) and not cached: %(p)s", t=(time.clock()-start), p=provider, logLevel=_TRACE)
                return provider
            except NotSupportedError as error:
                # An exception is normal here, just try the next factory.
                log.msg("DeviceManager: buildProvider: DeviceFactory does not supported URI: %(p)s", p=factory, logLevel=_TRACE)
                continue
            except ValueError as error:
                # Log the exception and then raise it again.
                log.msg("DeviceManager: buildProvider: DeviceFactory raised exception: %(e)s", e=error, logLevel=_TRACE)
                raise error
        raise NotSupportedError("Manager has no factory that supports the specified URI")


    def _pop_provider_cache(self, uri):
        if self._maxCacheSize > 0:
            if uri in self._provider_cache:
                return self._provider_cache[uri]
        return None


    def _push_provider_cache(self, uri, provider):
        if self._maxCacheSize > 0:
            self._provider_cache[uri] = provider
            if self._maxCacheSize < len(self._provider_cache):
                self._provider_cache.popitem(False)


    def _clear_provider_cache(self):
        if self._maxCacheSize > 0:
            self._provider_cache.clear()
