# coding=UTF-8
'''
Utility classes for multiplexing Protocols.
'''

from ..util import log

from twisted.internet import protocol

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class DistributingProtocolFactoryCanceller:

    def __init__(self):
        self.cancelled = False

    def cancel(self, deferred):
        self.cancelled = True
        deferred.errback()


class DistributingProtocolFactory(protocol.Factory):
    '''
    ProtocolFactory to build a DistributingProtocol. 
    '''
    
    def __init__(self, protocolFactories):
        self._protocolFactories = protocolFactories
    

    def buildProtocol(self, addr):
        protocols = []
        for protocolFactory in self._protocolFactories:
            protocol = protocolFactory.buildProtocol(addr)
            log.msg('DistributingProtocolFactory: buildProtocol: Built protocol %(p)s', p=protocol, logLevel=_TRACE)
            protocols.append(protocol)
        protocol = DistributingPrococol(addr, protocols)
        log.msg('DistributingProtocolFactory: buildProtocol: Built distributing protocol %(p)s', p=protocol, logLevel=_DEBUG)
        return protocol


class DistributingProtocol(protocol.Protocol):
    '''
    Protocol to distribute events to a list of protocols.
    '''
    
    def __init__(self, address, protocols):
        self._address = address
        self._protocols = protocols
        self._connected = False
        self.transport = None
    

    def dataReceived(self, data):
        log.msg('DistributingProtocol: dataReceived: Data type: %(t)s', t=type(data), logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('DistributingProtocol: dataReceived: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.dataReceived(data)
    
    
    def connectionLost(self, reason):
        self._connected = False
        log.msg('DistributingProtocol: connectionLost: Reason is %(r)s', r=reason, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('DistributingProtocol: connectionLost: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.connectionLost(reason)
    
        
    def makeConnection(self, transport):
        self.transport = transport
        log.msg('DistributingProtocol: makeConnection: Transport is %(t)s', t=transport, logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('DistributingProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.makeConnection(DistributingTransport(transport))
    

    def connectionMade(self):
        self._connected = True
        log.msg('DistributingProtocol: connectionMade: Log connection established', logLevel=_DEBUG)
        for protocol in self._protocols:
            log.msg('DistributingProtocol: makeConnection: Distribute to %(p)s', p=protocol, logLevel=_TRACE)
            protocol.connectionMade()


class DistributingTransport:
    '''
    Transport to properly handle removing protocol from a DistributingProtocol.
    '''
 
    def __init__(self, transport):
        self._transport = transport
 
 
    def write(self, data):
        log.msg("DistributingTransport: write: Delegate to transport %(t)s data type: %(d)s", t=self._transport, d=type(data), logLevel=_DEBUG)
        self._transport.write(data)


    def writeSequence(self, data):
        log.msg("DistributingTransport: writeSequence: Delegate to transport %(t)s data type: %(d)s", t=self._transport, d=type(data), logLevel=_DEBUG)
        self._transport.writeSequence(data)
    
    
    def loseConnection(self):
        log.msg("DistributingTransport: loseConnection: Delegate to transport %(t)s", t=self._transport, logLevel=_DEBUG)
        self._transport.loseConnection()
                

    def getPeer(self):
        log.msg("DistributingTransport: getPeer: Delegate to transport %(t)s", t=self._transport, logLevel=_DEBUG)
        return self._transport.getPeer()
    
    
    def getHost(self):
        log.msg("DistributingTransport: getHost: Delegate to transport %(t)s", t=self._transport, logLevel=_DEBUG)
        return self._transport.getHost()
