# coding=UTF-8
'''
Implementation of Twisted ClientEndpoint interface for an EPICS Process Variable (PV).
'''

import socket

from epics import pv, ca

from ..util import log

from twisted.internet import reactor, defer

_TRACE = log.TRACE
_DEBUG = log.DEBUG
_WARN = log.WARN


class ProcessVariableClientEndpoint:
    '''
    ClientEndpoint for connecting to a Channel Access 'Channel'. 
    '''

    def __init__(self, pvname):
        self.pvname = pvname

    
    def connect(self, protocolFactory):
        log.msg("ProcessVariableClientEndpoint: connect: Protocol factory %(p)s", p=protocolFactory, logLevel=_DEBUG)
        canceller = _ProcesssVariableCanceller()
        deferred = defer.Deferred(canceller.cancel)
        canceller.connector = _ProcessVariableConnector(self.pvname, canceller, deferred, protocolFactory)
        log.msg("ProcessVariableClientEndpoint: connect: Process Variable Connector %(c)s", c=canceller.connector, logLevel=_DEBUG)
        reactor.callLater(0, canceller.connector.connect)
        return deferred
        

class _ProcesssVariableCanceller:
    '''
    Cancel pending connection to a Process Variable. 
    '''
    
    def __init__(self):
        self.cancelled = False
        self.connector = None
    
    def cancel(self, deferred):        
        self.cancelled = True
        if self.connector is not None:
            self.connector.stopConnecting()
        deferred.errback()


class _ProcessVariableConnector:
    '''
    Adapt Process Variable callbacks to Twisted Protocol interface.
    '''
    
    def __init__(self, pvname, canceller, deferred, protocolFactory):
        self._pvname = pvname
        self._canceller = canceller
        self._deferred = deferred
        self._protocolFactory = protocolFactory
        self._protocol = None
        self._connected = False
        self._data = None
        self._pv = None


    def connect(self):
        if self._canceller.cancelled:
            log.msg("_ProcessVariableConnector: connect: Connection cancelled.", logLevel=_TRACE)
            return
        
        log.msg("_ProcessVariableConnector: connect: PV: %(p)s", p=self._pvname, logLevel=_DEBUG)
        self._pv = pv.PV(self._pvname, callback=self._pvValueCallback, connection_callback=self._pvConnCallback)


    def disconnect(self):
        log.msg("_ProcessVariableConnector: disconnect: PV: %(p)s", p=self._pvname, logLevel=_DEBUG)
        
        if self._pv is not None:
            self._pv.disconnect()
            self._pv = None

        if self._protocol is not None:
            self._protocol.connectionLost("Process Variable disconncted cleanly.")
            self._protocol = None


    def stopConnecting(self):
        if self._pv is not None and self._protocol is not None:
            self._pv.disconnect()
            self._pv = None


    def getDestination(self):
        return self._pvname


    def _pvConnCallback(self, **kwargs):
        '''
        Ensure thread safety by executing callback in reactor thread.
        '''
        reactor.callFromThread(self._connCallback, **kwargs)
    
    
    def _connCallback(self, **kwargs):
        '''
        Actually handle Process Variable connection callback.
        
        The keyword arguments are: 'pv', 'pvname', 'conn'.

        '''
        log.msg("_ProcessVariableConnector: _connCallback: Protocol is %(p)s", p=self._protocol, logLevel=_DEBUG)
        
        try:
            pv = kwargs['pv']
        except KeyError:
            log.msg("_ProcessVariableConnector: _connCallback: Key 'pv' not found!", logLevel=_WARN)
            return
        
        if self._pv is not pv:
            log.msg("_ProcessVariableConnector: _connCallback: PV does not match! (%(pv1)s != %(pv2)s)", pv1=id(pv), pv2=id(self._pv), logLevel=_WARN)
            pv = self._pv
        
        try:
            conn = kwargs['conn']
        except KeyError:
            log.msg("_ProcessVariableConnector: _connCallback: Key 'conn' not found!", logLevel=_WARN)
            return
        
        if self._connected == conn:
            pass
            
        elif conn == True:
            log.msg("_ProcessVariableConnector: _connCallback: Process Variable (Re)connected", logLevel=_DEBUG)
            self._connected = True
            if self._protocol is None:
                #
                self._protocol = self._protocolFactory.buildProtocol(self._pvname)
                log.msg("_ProcessVariableConnector: _connCallback: Build protocol: %(p)s", p=self._protocol, logLevel=_DEBUG)
                self._deferred.callback(self._protocol)
                #
                transport = _ProcessVariableTransport(pv, self)
                log.msg("_ProcessVariableConnector: _connCallback: Make connection %(t)s", t=transport, logLevel=_DEBUG)
                self._protocol.makeConnection(transport)
            self._protocol.connectionMade()
            # Normally when a PV (re)connects a value change follows so calling _valueCallback is redundant.
            #if self._data is not None:
            #    data['connected'] == True
            #    self._valueCallback(**self._data)
            
        elif conn == False:
            log.msg("_ProcessVariableConnector: _connCallback:  Process Variable NOT connected", logLevel=_DEBUG)
            self._connected = False
            # Indicate the process variable is not connected by resending the data with property 'connected' as False.
            if self._data is not None:
                self._valueCallback(**self._data)
            self._protocol.connectionLost("Process Variable lost connection.")
    

    def _pvValueCallback(self, **kwargs):
        '''
        Ensure thread safety by executing callback in reactor thread.
        '''
        reactor.callFromThread(self._valueCallback, **kwargs)
        
        
    def _valueCallback(self, **kwargs):
        '''
        Actually handle Channel Access value callback.
        '''
        
        if self._data is None:
            self._data = {}

        self._data.update(kwargs)

        # Transformation/Sanitization of the data
        # parameters can be done here if required.

        # Delete 'cb_info' because it contains
        # values that cannot be serialized to JSON.
        del self._data['cb_info']

        # Ensure connection status is
        # synchronized with the data set.
        self._data['connected'] = self._connected

        if self._protocol is not None:
            log.msg("_ProcessVariableConnector: _valueCallback: Call dataReceived %(p)s", p=self._protocol, logLevel=_TRACE)
            self._protocol.dataReceived(self._data)
        else:
            log.msg("_ProcessVariableConnector: _valueCallback: Protocol is None. It should have been initialized!", logLevel=_WARN)
    

class _ProcessVariableTransport:
    '''
    Implementation of Twisted Transport interface for a Process Variable.
    '''
    
    def __init__(self, pv, connector):
        self._pv = pv
        self._connector = connector

    
    def write(self, data):
        log.msg("_ProcessVariableTransport: write: Method not yet implemented.", logLevel=_WARN)
        #self._pv.put()
    

    def writeSequence(self, data):
        log.msg("_ProcessVariableTransport: writeSequence: Method not yet implemented.", logLevel=_WARN)
        #self._pv.put()

    
    def loseConnection(self):
        log.msg("_ProcessVariableTransport: loseConnection: Connector: %(c)s", c=self._connector, logLevel=_DEBUG)
        self._connector.disconnect()
    

    def getPeer(self):
        peer = self._pv.host
        log.msg("_ProcessVariableTransport: getPeer: Peer is %(p)s", p=peer, logLevel=_DEBUG)
        return peer

     
    def getHost(self):
        host = socket.gethostname()
        log.msg("_ProcessVariableTransport: getHost: Host is %(h)s", h=host, logLevel=_DEBUG)
        return host
