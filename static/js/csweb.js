/*
 * Utility classes and functions to support CSWeb UI.
 */

var csweb = {};

/*
 * WebSocket implementation that adds some conveniences such as auto-reconnect. 
 */
csweb.WebSocket = function(url, protocol) {
	this.url = url;
	this.protocol = protocol;
	this.pending = [];
	this.connect.call(this);
	this.readyState = csweb.WebSocket.CONNECTION;
};


csweb.WebSocket.CONNECTING = WebSocket.CONNECTING;	//  0 	The connection is not yet open.
csweb.WebSocket.OPEN       = WebSocket.OPEN; 		//	1 	The connection is open and ready to communicate.
csweb.WebSocket.CLOSING    = WebSocket.CLOSING; 	// 	2 	The connection is in the process of closing.
csweb.WebSocket.CLOSED     = WebSocket.CLOSED;		//	3 	The connection is closed or couldn't be opened.


csweb.WebSocket.prototype.connect = function() {
	
	var self = this;
	
	if(self.protocol == undefined) {
		self.ws = new WebSocket(self.url);
	} else {
		self.ws = new WebSocket(self.url, self.protocol);
	}

	this.ws.onopen = function(event) {
		self.readyState = csweb.WebSocket.OPEN;
		self.handleOnOpen.call(self, event);
	};
	
	this.ws.onmessage = function(event) {
		//alert("Got Message!");
		self.handleOnMessage.call(self, event);
	};
	
	self.ws.onerror = function(event) {
		self.readyState = csweb.WebSocket.CLOSING;
		self.handleOnOpen.call(self, event);
		setTimeout(function() {
			console.log("Try to connect Again!");
			self.connect();
		}, 10000);
	};
	
	self.ws.onclose = function(event) {
		self.readyState = csweb.WebSocket.CLOSED;
		console.log(event);
		self.handleOnClose.call(self, event);
	};
};

csweb.WebSocket.prototype.handleOnOpen = function(event) {
	var self = this;
	setTimeout(function() {
		self.doSendPending();
	}, 0);
	// TODO: Trigger event using native JavaScript 
	//       to remove dependency on jQuery library. 
	$(this).trigger(jQuery.Event(event));
};

csweb.WebSocket.prototype.handleOnMessage = function(event) {
	var e = jQuery.Event(event);
	// jQuery makes special use of the 'event.data'
	// property. Use the 'event.message' property
	// instead to contain the received data.
	e.message = event.data;
	// TODO: Trigger event using native JavaScript 
	//       to remove dependency on jQuery library.
	$(this).trigger(e);
};

csweb.WebSocket.prototype.handleOnError = function(event) {
	// TODO: Trigger event using native JavaScript 
	//       to remove dependency on jQuery library. 
	$(this).trigger(jQuery.Event(event));
};

csweb.WebSocket.prototype.handleOnClose = function(event) {
	// TODO: Trigger event using native JavaScript 
	//       to remove dependency on jQuery library. 
	$(this).trigger(jQuery.Event(event));
};

csweb.WebSocket.prototype.subscribe = function(uri) {
	var self = this;
	setTimeout(function() {
		self.send('SUB ' + encodeURI(uri));
	}, 100);
};

csweb.WebSocket.prototype.send = function(data, force) {
	if(!this.doSend(data)) {
		console.log("Pend msg: " + data);
		this.pending.push(data);
	}
};

csweb.WebSocket.prototype.doSendPending = function() {
	while(this.pending.length > 0) {
		var data = this.pending.shift();
		if(!this.doSend(data)) {
			this.pending.unshift(data);
			break;
		}
	}
};

csweb.WebSocket.prototype.doSend = function(data) {
	if(this.ws && (this.ws.readyState == this.ws.OPEN)) {
		console.log("Msg Sent: " + data);
		this.ws.send(data);
		return true;
	}
	return false;
};
