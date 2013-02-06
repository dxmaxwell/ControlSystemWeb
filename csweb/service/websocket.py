# coding=UTF-8
'''
WebSocket protocol to handles device requests.
'''

from .. import device

from ..util import log, json
from ..util.request import CSWPRequest

from twisted.internet import protocol

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class WebSocketDeviceProtocolFactory(protocol.Factory):
    '''
    Protocol factory for WebSocketDeviceProtocol.
    '''

    def buildProtocol(self, addr):
        return WebSocketDeviceProtocol()


class WebSocketDeviceProtocol(protocol.Protocol):
    '''
    Protocol to handle CSWP request from Web Socket clients.
    '''
    
    def __init__(self):
        self._subscriptions = {}
    

    def connectionMade(self):
        log.msg("WebSocketDeviceProtocol: connectionMade: Log connection established.", logLevel=_DEBUG)
        
    
    def dataReceived(self, data):
        log.msg("WebSocketDeviceProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_DEBUG)
        request = CSWPRequest(data)
        log.msg("WebSocketDeviceProtocol: dataReceived: CSWP request %(r)s", r=request, logLevel=_TRACE)
        if request.action == 'SUB':
            self._handleSubscribe(request)
        else:
            log.msg("WebSocketDeviceProtocol: dataReceived: Requested action not supported %(r)s", r=request, debugLevel=_WARN)


    def connectionLost(self, reason):
        log.msg("WebSocketDeviceProtocol: connectionLost: Reason %(r)s", r=reason, logLevel=_DEBUG)
        for subscription in self._subscriptions.values():
            log.msg("WebSocketDeviceProtocol: connectionLost: Call loseConnection %(s)s", s=subscription, logLevel=_TRACE)
            subscription.loseConnection()
        self._subscriptions.clear()  # Clear list of Subscription Protocols.
    

    def _handleSubscribe(self, request):
        if request.url not in self._subscriptions:
            log.msg("WebSocketDeviceProtocol: _handleSubscribe: No subsciption for URL %(r)s", r=request, logLevel=_DEBUG)
            protocolFactory = WSDeviceSubscriptionProtocolFactory(request.url, self)
            deferred = device.subscribe(request.url, protocolFactory)
            subscription = _WebSocketDeviceSubscription(deferred)
            log.msg("WebSocketDeviceProtocol: _handleSubscribe: Add subsciption %(s)s", s=subscription, logLevel=_TRACE)
            self._subscriptions[request.url] = subscription
        else:
            log.msg("WebSocketDeviceProtocol: _handleSubscribe: Subsciption found for URL %(r)s", r=request, logLevel=_TRACE)
            self._subscriptions[request.url].writeData()


class _WebSocketDeviceSubscription:

    def __init__(self, deferred):
        self._protocol = None
        self._deferred = deferred
        self._deferred.addCallback(self._subscribeCallback)
        self._deferred.addErrback(self._subscribeErrback)


    def writeData(self):
        if self._protocol is not None:
            log.msg("_WebSocketDeviceSubscription: writeData: Protocol %(p)s", p=self._protocol, logLevel=_TRACE)
            self._protocol.writeData()
        else:
            log.msg("_WebSocketDeviceSubscription: writeData: Protocol has not been initialized", logLevel=_DEBUG)


    def loseConnection(self):
        if self._protocol is not None:
            log.msg("_WebSocketDeviceSubscription: loseConnection: Protocol %(p)s", p=self._protocol, logLevel=_DEBUG)
            self._protocol.transport.loseConnection()
        else:
            log.msg("_WebSocketDeviceSubscription: loseConnection: Deferred %(d)s", d=self._deferred, logLevel=_DEBUG)
            self._deferred.cancel()


    def _subscribeCallback(self, protocol):
        log.msg("_WebSocketDeviceSubscription: _subscribeCallback: Protocol %(p)s", p=protocol, logLevel=_DEBUG)
        self._protocol = protocol
        
        
    def _subscribeErrback(self, failure):
        log.msg("_WebSocketDeviceSubscription: _subscribeErrback: Failure %(f)s", f=failure, logLevel=_DEBUG)



class WSDeviceSubscriptionProtocol(protocol.Protocol):
    '''
    Protocol to handle a device subscription.
    '''
    
    def __init__(self, url, wssp):
        self._url = url
        self._wssp = wssp
        self._data = None


    def connectionMade(self):
        log.msg("WSDeviceSubscriptionProtocol: connectionMade: Log connection established", logLevel=_DEBUG)
            
    
    def dataReceived(self, data):
        log.msg("WSDeviceSubscriptionProtocol: dataReceived: Data type %(t)s", t=type(data), logLevel=_TRACE)
        self._data = { self._url : data }
        self.writeData()
    

    def connectionLost(self, reason):
        log.msg("WSDeviceSubscriptionProtocol: connectionLost: Reason %(r)s", r=reason, logLevel=_DEBUG)
        #What to do here?


    def makeConnection(self, transport):
        log.msg("WSDeviceSubscriptionProtocol: makeConnection: Transport %(t)s", t=transport, logLevel=_DEBUG)
        self.transport = transport


    def writeData(self):
        if self._data is not None:
            log.msg("WSDeviceSubscriptionProtocol: writeData: Write data to WebSocket as JSON", logLevel=_TRACE)
            try: 
                jsondata = json.stringify(self._data, sanitize=True)
            except Exception as e:
                log.msg("WSDeviceSubscriptionProtocol: dataReceived: Error dumping JSON: %(e)s", e=e, logLevel=_WARN)
                return
            self._wssp.transport.write(jsondata)

        else:
            log.msg("WSDeviceSubscriptionProtocol: writeData: Data has not been initialized.", logLevel=_WARN)


class WSDeviceSubscriptionProtocolFactory(protocol.Factory):
    '''
    Protocol factory for WSDeviceSubscriptionProtocol.
    '''

    def __init__(self, url, wssp):
        self._url = url
        self._wssp = wssp


    def buildProtocol(self, addr):
        return WSDeviceSubscriptionProtocol(self._url, self._wssp)
