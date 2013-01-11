# coding=UTF-8
'''
DeviceProvider interface for EPICS PVs.

Supported URL:
    epics:ProcessVariable[?[buffer=<size>][&[rate=<interval>]|[ratelimit=<interval>]]]

Supported Parameters:
    buffer=<size>
    rate=<interval>
    ratelimit=<interval>
'''

from urllib import urlencode
from urlparse import urlsplit, urlunsplit, parse_qsl


from .subs.client import EpicsClientSubscription
from .subs.buffer import EpicsBufferSubscription
from .subs.rate import EpicsRateSubscription
from .subs.rate import EpicsRateLimitSubscription

from ..util.url import URL
from ..util import log, dist

from ..device.provider import DeviceProvider
from ..device.manager import NotSupportedError

from twisted.internet import defer, protocol, reactor

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN

_EPICS_DEFAULT_SCHEME = 'epics'
_EPICS_PARAM_BUFFER = 'buffer'
_EPICS_PARAM_RATE = 'rate'
_EPICS_PARAM_RATE_LIMIT = 'ratelimit'



class EpicsDeviceProvider(DeviceProvider):
    '''
    Implementation of DeviceProvider interface for accessing EPICS Channel Access.
    '''

    def __init__(self, scheme=_EPICS_DEFAULT_SCHEME):
        URL.register_scheme(scheme)
        self._subscriptions = {}
        self._scheme = scheme


    def subscribe(self, url, protocolFactory):
        '''
        Subscribe to the specified EPICS PV.  
        '''
        try:
            url = self._supports(url)
            log.msg("EpicsDeviceProvider: subscribe: Supported URI: %(u)s", u=url, logLevel=_DEBUG)
        except Exception as fail:
            log.msg("EpicsDeviceProvider: subscribe: Unsuppored URI: %(u)s", u=url, logLevel=_WARN)
            # return something!


        query = dict(url.query)
        url.query.clear()

        if str(url) in self._subscriptions:
            subscription = self._subscriptions[str(url)]
        else:
            pvname = URL.decode(url.path)
            subscription = EpicsClientSubscription(pvname, str(url), self._subscriptions)

        if _EPICS_PARAM_RATE in query:
            url.query[_EPICS_PARAM_RATE] = query[_EPICS_PARAM_RATE]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
            else:
                interval = query[_EPICS_PARAM_RATE]
                subscription = EpicsRateSubscription(subscription, interval, str(url), self._subscriptions)

        if _EPICS_PARAM_RATE_LIMIT in query:
            url.query[_EPICS_PARAM_RATE_LIMIT] = query[_EPICS_PARAM_RATE_LIMIT]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
            else:
                interval = query[_EPICS_PARAM_RATE_LIMIT]
                subscription = EpicsRateLimitSubscription(subscription, interval, str(url), self._subscriptions)

        if _EPICS_PARAM_BUFFER in query:
            url.query[_EPICS_PARAM_BUFFER] = query[_EPICS_PARAM_BUFFER]
            if str(url) in self._subscriptions:
                subscription = self._subscriptions[str(url)]
            else:
                size = query[_EPICS_PARAM_BUFFER]
                subscription = EpicsBufferSubscription(subscription, size, str(url), self._subscriptions)

        return subscription.addProtocolFactory(protocolFactory)


    def _supports(self, url):
        url = URL(url)
        if url.scheme != self._scheme:
            raise NotSupportedError("Scheme (%s) not supported by EpicsDeviceProvider" % (result.scheme))

        url.path = url.path.strip('/')
        if url.path == '':
            raise NotSupportedError("Path is empty, process variable must be specified")

        url.merge_params()
        url.params.set_sort_keys()
        url.params.set_lower_keys()
        url.params.retain((_EPICS_PARAM_RATE_LIMIT,_EPICS_PARAM_RATE,_EPICS_PARAM_BUFFER))

        if _EPICS_PARAM_RATE in url.query and _EPICS_PARAM_RATE_LIMIT in url.query:
            raise NotSupportedError("Parameters '%s' and '%s' are mutually exclusive" % (_EPICS_PARAM_RATE,_EPICS_PARAM_RATE_LIMIT))

        if _EPICS_PARAM_RATE in url.query:
            try:
                url.query[_EPICS_PARAM_RATE] = float(url.query[_EPICS_PARAM_RATE])
            except:
                raise NotSupportedError("Parameter (%s) non-integer value (%s)" % (_EPICS_PARAM_RATE,url.query[_EPICS_PARAM_RATE]))
            if url.query[_EPICS_PARAM_RATE] <= 0.0:
                raise NotSupportedError("Parameter (%s) value <= 0.0 (%d)" % (_EPICS_PARAM_RATE,url.query[_EPICS_PARAM_RATE]))

        if _EPICS_PARAM_RATE_LIMIT in url.query:
            try:
                url.query[_EPICS_PARAM_RATE_LIMIT] = float(url.query[_EPICS_PARAM_RATE_LIMIT])
            except:
                raise NotSupportedError("Parameter (%s) non-integer value (%s)" % (_EPICS_PARAM_RATE_LIMIT,url.query[_EPICS_PARAM_RATE_LIMIT]))
            if url.query[_EPICS_PARAM_RATE_LIMIT] <= 0.0:
                raise NotSupportedError("Parameter (%s) value <= 0.0 (%d)" % (_EPICS_PARAM_RATE_LIMIT,url.query[_EPICS_PARAM_RATE_LIMIT]))

        if _EPICS_PARAM_BUFFER in url.query:
            try:
                url.query[_EPICS_PARAM_BUFFER] = int(url.query[_EPICS_PARAM_BUFFER])
            except ValueError:
                raise NotSupportedError("Parameter (%s) non-integer value (%s)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))
            if url.query[_EPICS_PARAM_BUFFER] < 1:
                raise NotSupportedError("Parameter (%s) value < 1 (%d)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))
            if url.query[_EPICS_PARAM_BUFFER] > 100000:
                raise NotSupportedError("Parameter (%s) value > 100000 (%d)" % (_EPICS_PARAM_BUFFER,url.query[_EPICS_PARAM_BUFFER]))

        return url


    def supports(self, url):
        try:
            self._supports(url)
            return True
        except NotSupportedError:
            return False
