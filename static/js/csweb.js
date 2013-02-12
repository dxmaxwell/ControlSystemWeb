//
// Utility classes and functions to support CSWUI.
//

var csweb = {};


(function() {
//
// Utility class to help with construction of URIs.
// If parsing URI is ever required then consider
// one of the available JS libraries.
//
	var URI = function() {

		if( !(this instanceof URI) ) {
			return new URI();
		}

		this.scheme = '';
		this.host = '';
		this.port = '';
		this.path = '';
		this.query = {};
		this.username = '';
		this.password = '';
	}

	csweb.URI = URI;

	var isStr = function(obj) {
		return (obj !== undefined) && (obj !== null) &&
				(typeof obj === 'string') && (obj.length > 0);
	};

	var isObj = function(obj) {
		return (obj !== undefined) && (obj !== null) &&
				(typeof obj === 'object') && (obj.length === undefined);
	};

	var isArr = function(obj) {
		return (obj !== undefined) && (obj !== null) &&
				(typeof obj === 'object') && (obj.length !== undefined);
	};

	var isNum = function(obj) {
		return (obj !== undefined) && (obj !== null) &&
				(typeof obj === 'number');
	}

	URI.prototype.toString = function() {

		var url = '';

		if( isStr(this.scheme) ) {

			if( isStr(this.scheme) ) {
				url += this.scheme+':';
			}
			
			if( isStr(this.host) ) {

				url += '//';

				if( isStr(this.username) ) {
					
					url += this.username;
					
					if( isStr(this.password) ) {
						url += ':'+this.password;
					}

					url += '@';
				}

				url += this.host+'/';

				if( isStr(this.port) || isNum(this.port) ) {
					url += ':'+this.port;
				}
			}
		}

		if( isStr(this.path) ) {
			url += encodeURIComponent(this.path);
		}
		else if( isArr(this.path) ) {
			for( var idx=0; idx<this.path.length; idx++ ) {
				url += encodeURIComponent(this.path[idx]);
			}
		}

		if( isStr(this.query) ) {
			url += '?'+this.query;
		}
		else if( isObj(this.query) ) {
			var prefix = '?';
			for(var key in this.query) {
				url += prefix + encodeURIComponent(key) + '=' + encodeURIComponent(this.query[key]);
				prefix = '&';
			}
		}
		
		return url;
	};

})();



(function() {
//
// Simple implementation of an event dispatcher 
// mostly copied from SockJS client library.
//
	var EventDispatcher = function() {

		if( !(this instanceof EventDispatcher) ) {
			return new EventDispatcher();
		}

		this._listeners = {};
	}

	csweb.EventDispatcher = EventDispatcher;

	EventDispatcher.prototype.addEventListener = function(eventType, listener) {
		if( (eventType !== undefined) && (typeof eventType !== 'string') ) {
			eventType = eventType.toString();
		}
		if( !(eventType in this._listeners) ) {
			this._listeners[eventType] = [];
		}
		var listeners = this._listeners[eventType];
		for( var idx=0; idx<listeners.length; idx++ ) {
			if( listener === listeners[idx] ) {
				return;
			}
		}
		listeners.push(listener);
		return;
	};

	EventDispatcher.prototype.removeEventListener = function(eventType, listener) {
		if( (eventType !== undefined) && (typeof eventType !== 'string') ) {
			eventType = eventType.toString();
		}
		if( !(eventType in this._listeners) ) {
			return;
		}
		var listeners = this._listeners[eventType];
		for( var idx=0; idx<listeners.length; idx++ ) {
			if( listener === listeners[idx] ) {
				if( listeners.length > 1 ) {
					this._listeners[eventType] = listeners.slice(0, idx).concat(listeners.slice(idx+1));
				} else {
					delete this._listeners[eventType];
				}
				return;
			}
		}
		return;
	};

	EventDispatcher.prototype.dispatchEvent = function(event) {
		if( event.type === undefined ) {
			return;
		}
		var t = event.type;
		var h = 'on' + t;
		if( (this[h] !== undefined) && (typeof this[h] === 'function') ) {
			try {
				this[h].call(this, event);
			}
			catch(e) {
				console.log('Exception while dispatching handler, ' + h + '. ' + e);
			}
		}
		if( t in this._listeners ) {
			var listeners = this._listeners[t];
			for(var idx=0; idx<listeners.length; idx++) {
				if( (listeners[idx] !== undefined) && (typeof listeners[idx] === 'function') ) {
					try {
						listeners[idx].call(this, event);
					}
					catch(e) {
						console.log('Exception while dispatching listener. ' + e);
					}
				}
			}
		}
		return;
	};
	
})();



(function () {
//
// WebSocket implementation that adds 
// conveniences such as auto-reconnect
// and specialized send methods.
//
	var Socket = function(url, protocol) {
		
		if( !(this instanceof Socket) ) {
			return new Socket(url, protocol);
		}

		csweb.EventDispatcher.call(this);

		this.url = url;
		this.protocol = protocol;
		this.readyState = WebSocket.CONNECTING;

		this._socket = null;
		this._pending = [];
		this._reconnectDelay = Socket.reconnectDelay*1000; // convert seconds to milliseconds
		this._reconnectAttempts = Socket.reconnectAttempts;

		if( url === undefined ) {
			return;
		}

		this._connect();
	};


	csweb.Socket = Socket;

	Socket.autoReconnect = true; 	// Try to auto-reconnect?
	Socket.reconnectDelay = 5;		// Minimum delay between attempts in seconds (10s, 20s, 40s,...).
	Socket.reconnectAttempts = 20;	// Maximum number of times to attempt to reconnect socket.

	Socket.CONNECTING = WebSocket.CONNECTING;	//  0 	The connection is not yet open.
	Socket.OPEN       = WebSocket.OPEN;			//	1 	The connection is open and ready to communicate.
	Socket.CLOSING    = WebSocket.CLOSING;		// 	2 	The connection is in the process of closing.
	Socket.CLOSED     = WebSocket.CLOSED;		//	3 	The connection is closed or couldn't be opened.


	Socket.prototype = new csweb.EventDispatcher();
	Socket.prototype.superclass = csweb.EventDispatcher;
	Socket.prototype.constructor = Socket;


	Socket.prototype._connect = function() {

		if(this.protocol === undefined) {
			this._socket = new WebSocket(this.url);
		} else {
			this._socket = new WebSocket(this.url, this.protocol);
		}

		this.readyState = this._socket.readyState;

		var self = this;

		this._socket.onopen = function(event) {
			self._socketOnOpen(event);
		};
		
		this._socket.onmessage = function(event) {
			self._socketOnMessage(event);
		};

		this._socket.onerror = function(event) {
			self._socketOnError(event);
		};
		
		this._socket.onclose = function(event) {
			self._socketOnClose(event);
		};
	}

	Socket.prototype._socketOnOpen = function(event) {
		this.readyState = this._socket.readyState;
		// Reset the auto reconnect properties. //
		this._reconnectDelay = Socket.reconnectDelay*1000; // convert seconds to milliseconds
		this._reconnectAttempts = Socket.reconnectAttempts;
		
		for( var idx=0; idx<this._pending.length; idx++ ) {
			this._socket.send(this._pending[idx]);
		}
		this._pending = [];

		this.dispatchEvent(event);
	};

	Socket.prototype._socketOnMessage = function(event) {		
		// An empty message is sent by the server to finalize
		// the connection with Windows clients. Ignore this message!
		if( (event.data === undefined) || (event.data.length === 0) ) {
			return;
		}
		this.dispatchEvent(event);
		// Attempt to parse data and dispatch the events. //
		try {
			var data = JSON.parse(event.data);
			for( var url in data ) {
				this.dispatchEvent({ type:url, data:data[url] });
			}
		} catch(e) {
			console.log('Unable to parse message as JSON.');
		}
	};

	Socket.prototype._socketOnError = function(event) {
		// Browser log the cause of this error to console. //
		this.readyState = this._socket.readyState;
		this.dispatchEvent(event);
	};

	Socket.prototype._socketOnClose = function(event) {
		this.readyState = this._socket.readyState;

		var self = this;
		if( (Socket.autoReconnect) && (this._reconnectAttempts > 0) ) {
			console.log("Attempt reconnect in: " + this._reconnectDelay + "ms (Remaining attempts: " + this._reconnectAttempts + ")");
			setTimeout(function() { self._connect(); }, this._reconnectDelay);
			this._reconnectDelay *= 2;
			this._reconnectAttempts -= 1;
		}

		this.dispatchEvent(event);
	};


	Socket.prototype._socketOnCloseRequested = function(event) {
		this.readyState = this._socket.readyState;
		this.dispatchEvent(event);
	};

	Socket.prototype.close = function() {
		this._socket.close();
		this.readyState = this._socket.readyState;
		// WebSocket.close() does not dispatch the 'close'
		// event. Dispatch it here explicitly so that UI
		// elements are aware that the socket is closed.
		var event = { type:'close' };
		this.dispatchEvent(event);
	};

	Socket.prototype.send = function(data) {
		if( this.readyState === Socket.OPEN ) {
			console.log("Msg Sent: " + data);
			this._socket.send(data);
		} else {
			console.log("Pend msg: " + data);
			this._pending.push(data);
		}
	};

	Socket.prototype.subscribe = function(uri) {
		this.send('SUB '+uri);
	};

})();
