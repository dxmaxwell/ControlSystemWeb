# coding=UTF-8
'''
DeviceProvider interface for EPICS PVs.

Supported URL:
    epics:ProcessVariable[?[buffer=<size>][&[rate=<interval>]|[ratelimit=<interval>][&lowedge=<value>][&highedge=<value>][&threshold=<value>][&name=<value>][&units=<value>][&precision=<value>][&scale=<value>][&offset=<value>]]]

Supported Parameters:
    buffer=<size>
    rate=<interval>
    ratelimit=<interval>
    lowedge=<value>
    highedge=<value>
    threshold=<value>
    name=<value>
    units=<value>
    precision=<value>
    scale=<value>
    offset=<value>
'''

from .subs.client import EpicsClientSubscription
from .subs.buffer import EpicsBufferSubscription
from .subs.rate import EpicsRateSubscription
from .subs.rate import EpicsRateLimitSubscription
from .subs.filter import EpicsLowEdgeSubscription
from .subs.filter import EpicsHighEdgeSubscription
from .subs.filter import EpicsThresholdSubscription
from .subs.set import EpicsSetSubscription
from .subs.set import EpicsSetPrecisionSubscription
from .subs.scale import EpicsScaleSubscription
from .subs.scale import EpicsOffsetSubscription

from ..util.url import URL
from ..util import log

from ..device.provider import DeviceProvider, DeviceFactory, NotSupportedError


_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN

_EPICS_DEFAULT_SCHEME = 'epics'
_EPICS_PARAM_BUFFER = 'buffer'
_EPICS_PARAM_RATE = 'rate'
_EPICS_PARAM_RATE_LIMIT = 'ratelimit'
_EPICS_PARAM_LOWEDGE = 'lowedge'
_EPICS_PARAM_HIGHEDGE = 'highedge'
_EPICS_PARAM_THRESHOLD = 'threshold'
_EPICS_PARAM_NAME = 'name'
_EPICS_PARAM_UNITS = 'units'
_EPICS_PARAM_PRECISION = 'precision'
_EPICS_PARAM_SCALE = 'scale'
_EPICS_PARAM_OFFSET = 'offset'


class EpicsDeviceProvider(DeviceProvider):
    '''
    Implementation of DeviceProvider interface for accessing EPICS Channel Access.
    '''

    def __init__(self, subscriptions, url):
        self._subscriptions = subscriptions
        self._url = url
        

    def subscribe(self, protocolFactory):
        '''
        Subscribe to the specified EPICS PV.  
        '''

        url = URL(self._url)
        query = dict(url.query)
        url.query.clear()

        if str(url) in self._subscriptions:
            subscription = self._subscriptions[str(url)]
            log.msg("EpicsDeviceProvider: subscribe: EpicsClientSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
        else:
            pvname = URL.decode(url.path)
            subscription = EpicsClientSubscription(pvname, str(url), self._subscriptions)
            log.msg("EpicsDeviceProvider: subscribe: EpicsClientSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_RATE in query:
            url.query[_EPICS_PARAM_RATE] = query[_EPICS_PARAM_RATE]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsRateSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                interval = query[_EPICS_PARAM_RATE]
                subscription = EpicsRateSubscription(subscription, interval, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsRateSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_SCALE in query:
            url.query[_EPICS_PARAM_SCALE] = query[_EPICS_PARAM_SCALE]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsScaleSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                value = query[_EPICS_PARAM_SCALE]
                subscription = EpicsScaleSubscription(subscription, value, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsScaleSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_OFFSET in query:
            url.query[_EPICS_PARAM_OFFSET] = query[_EPICS_PARAM_OFFSET]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsOffsetSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                value = query[_EPICS_PARAM_OFFSET]
                subscription = EpicsOffsetSubscription(subscription, value, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsOffsetSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_LOWEDGE in query:
            url.query[_EPICS_PARAM_LOWEDGE] = query[_EPICS_PARAM_LOWEDGE]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsLowEdgeSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                value = query[_EPICS_PARAM_LOWEDGE]
                subscription = EpicsLowEdgeSubscription(subscription, value, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsLowEdgeSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_HIGHEDGE in query:
            url.query[_EPICS_PARAM_HIGHEDGE] = query[_EPICS_PARAM_HIGHEDGE]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsHighEdgeSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                value = query[_EPICS_PARAM_HIGHEDGE]
                subscription = EpicsHighEdgeSubscription(subscription, value, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsHighEdgeSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_THRESHOLD in query:
            url.query[_EPICS_PARAM_THRESHOLD] = query[_EPICS_PARAM_THRESHOLD]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsThresholdSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                value = query[_EPICS_PARAM_THRESHOLD]
                subscription = EpicsThresholdSubscription(subscription, value, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsThresholdSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_RATE_LIMIT in query:
            url.query[_EPICS_PARAM_RATE_LIMIT] = query[_EPICS_PARAM_RATE_LIMIT]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsRateLimitSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                interval = query[_EPICS_PARAM_RATE_LIMIT]
                subscription = EpicsRateLimitSubscription(subscription, interval, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsRateLimitSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_NAME in query:
            url.query[_EPICS_PARAM_NAME] = query[_EPICS_PARAM_NAME]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetSubscription ('name') found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                name = query[_EPICS_PARAM_NAME]
                subscription = EpicsSetSubscription(subscription, "name", name, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetSubscription ('name') not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_UNITS in query:
            url.query[_EPICS_PARAM_UNITS] = query[_EPICS_PARAM_UNITS]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetSubscription ('units') found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                units = query[_EPICS_PARAM_UNITS]
                subscription = EpicsSetSubscription(subscription, "units", units, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetSubscription ('units') not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_PRECISION in query:
            url.query[_EPICS_PARAM_PRECISION] = query[_EPICS_PARAM_PRECISION]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetPrecisionSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                precision = query[_EPICS_PARAM_PRECISION]
                subscription = EpicsSetPrecisionSubscription(subscription, precision, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsSetPrecisionSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        if _EPICS_PARAM_BUFFER in query:
            url.query[_EPICS_PARAM_BUFFER] = query[_EPICS_PARAM_BUFFER]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
                log.msg("EpicsDeviceProvider: subscribe: EpicsBufferSubscription found for '%(u)s'", u=url, logLevel=_DEBUG)
            else:
                size = query[_EPICS_PARAM_BUFFER]
                subscription = EpicsBufferSubscription(subscription, size, str(url), self._subscriptions)
                log.msg("EpicsDeviceProvider: subscribe: EpicsBufferSubscription not found for '%(u)s'", u=url, logLevel=_DEBUG)

        return subscription.addProtocolFactory(protocolFactory)


class EpicsDeviceFactory(DeviceFactory):
    '''
    Implementation of DeviceFactory interface for accessing EPICS Channel Access.
    '''

    def __init__(self, scheme=_EPICS_DEFAULT_SCHEME, cacheable=True):
        self._scheme = scheme
        self._cacheable = cacheable
        self._subscriptions = {}
        URL.register_scheme(scheme)


    def cacheable(self):
        return self._cacheable


    def buildProvider(self, url):
        url = URL(str(url))
        if url.scheme != self._scheme:
            raise NotSupportedError("Scheme (%s) not supported by EpicsDeviceProvider" % (result.scheme))

        url.path = url.path.strip('/')
        if url.path == '':
            raise NotSupportedError("Path is empty, process variable must be specified")

        # The specified URL path (ie PV name) may or may not be URL encoded,
        # in order to normalize the path properly always decode then encode.
        url.path = URL.encode(URL.decode(url.path))

        url.merge_params()
        url.params.set_sort_keys()
        url.params.set_lower_keys()
        url.params.retain((_EPICS_PARAM_SCALE,_EPICS_PARAM_OFFSET,_EPICS_PARAM_LOWEDGE,_EPICS_PARAM_HIGHEDGE,_EPICS_PARAM_THRESHOLD,_EPICS_PARAM_RATE_LIMIT,_EPICS_PARAM_RATE,_EPICS_PARAM_NAME,_EPICS_PARAM_UNITS,_EPICS_PARAM_PRECISION,_EPICS_PARAM_BUFFER))

        if _EPICS_PARAM_RATE in url.query and _EPICS_PARAM_RATE_LIMIT in url.query:
            raise ValueError("Parameters '%s' and '%s' are mutually exclusive" % (_EPICS_PARAM_RATE,_EPICS_PARAM_RATE_LIMIT))

        if _EPICS_PARAM_RATE in url.query:
            try:
                url.query[_EPICS_PARAM_RATE] = float(url.query[_EPICS_PARAM_RATE])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_RATE,url.query[_EPICS_PARAM_RATE]))
            if url.query[_EPICS_PARAM_RATE] <= 0.0:
                raise ValueError("Parameter (%s) value <= 0.0 (%d)" % (_EPICS_PARAM_RATE,url.query[_EPICS_PARAM_RATE]))

        if _EPICS_PARAM_SCALE in url.query:
            try:
                url.query[_EPICS_PARAM_SCALE] = float(url.query[_EPICS_PARAM_SCALE])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_SCALE,url.query[_EPICS_PARAM_SCALE]))

        if _EPICS_PARAM_OFFSET in url.query:
            try:
                url.query[_EPICS_PARAM_OFFSET] = float(url.query[_EPICS_PARAM_OFFSET])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_OFFSET,url.query[_EPICS_PARAM_OFFSET]))

        if _EPICS_PARAM_LOWEDGE in url.query:
            try:
                url.query[_EPICS_PARAM_LOWEDGE] = float(url.query[_EPICS_PARAM_LOWEDGE])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_LOWEDGE,url.query[_EPICS_PARAM_LOWEDGE]))

        if _EPICS_PARAM_HIGHEDGE in url.query:
            try:
                url.query[_EPICS_PARAM_HIGHEDGE] = float(url.query[_EPICS_PARAM_HIGHEDGE])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_HIGHEDGE,url.query[_EPICS_PARAM_HIGHEDGE]))

        if _EPICS_PARAM_THRESHOLD in url.query:
            try:
                url.query[_EPICS_PARAM_THRESHOLD] = float(url.query[_EPICS_PARAM_THRESHOLD])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_THRESHOLD,url.query[_EPICS_PARAM_THRESHOLD]))

        if _EPICS_PARAM_RATE_LIMIT in url.query:
            try:
                url.query[_EPICS_PARAM_RATE_LIMIT] = float(url.query[_EPICS_PARAM_RATE_LIMIT])
            except:
                raise ValueError("Parameter (%s) non-numeric value (%s)" % (_EPICS_PARAM_RATE_LIMIT,url.query[_EPICS_PARAM_RATE_LIMIT]))
            if url.query[_EPICS_PARAM_RATE_LIMIT] <= 0.0:
                raise ValueError("Parameter (%s) value <= 0.0 (%d)" % (_EPICS_PARAM_RATE_LIMIT,url.query[_EPICS_PARAM_RATE_LIMIT]))

        if _EPICS_PARAM_NAME in url.query:
            try:
                url.query[_EPICS_PARAM_NAME] = str(url.query[_EPICS_PARAM_NAME])
            except:
                raise ValueError("Parameter (%s) non-string value (%s)" % (_EPICS_PARAM_NAME,url.query[_EPICS_PARAM_NAME]))

        if _EPICS_PARAM_UNITS in url.query:
            try:
                url.query[_EPICS_PARAM_UNITS] = str(url.query[_EPICS_PARAM_UNITS])
            except:
                raise ValueError("Parameter (%s) non-string value (%s)" % (_EPICS_PARAM_UNITS,url.query[_EPICS_PARAM_UNITS]))

        if _EPICS_PARAM_PRECISION in url.query:
            try:
                url.query[_EPICS_PARAM_PRECISION] = int(url.query[_EPICS_PARAM_PRECISION])
            except:
                raise ValueError("Parameter (%s) non-integer value (%s)" % (_EPICS_PARAM_PRECISION,url.query[_EPICS_PARAM_PRECISION]))
            if url.query[_EPICS_PARAM_PRECISION] < 0:
                raise ValueError("Parameter (%s) value < 0 (%d)" % (_EPICS_PARAM_PRECISION,url.query[_EPICS_PARAM_PRECISION]))

        if _EPICS_PARAM_BUFFER in url.query:
            try:
                url.query[_EPICS_PARAM_BUFFER] = int(url.query[_EPICS_PARAM_BUFFER])
            except ValueError:
                raise ValueError("Parameter (%s) non-integer value (%s)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))
            if url.query[_EPICS_PARAM_BUFFER] < 1:
                raise ValueError("Parameter (%s) value < 1 (%d)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))
            if url.query[_EPICS_PARAM_BUFFER] > 100000:
                raise ValueError("Parameter (%s) value > 100000 (%d)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))

        return EpicsDeviceProvider(self._subscriptions, url)
