/*
 * Control System Web User Interface.
 */

var cswui = {};


(function() {

	cswui.defaultDeviceProtocol = 'epics';

	cswui.socket = new csweb.Socket('ws://'+location.host+'/device/ws');

	cswui.fields = [];

	/*
	 * Process document for CSW elements.
	 */
	var process = function() {
		$('.csw-strip-chart').each(function(idx, elx) {
			cswui.fields.push(new cswui.StripChartField(elx));
		});
		$('.csw-readonly-field').each(function(idx, elx) {
			cswui.fields.push(new cswui.ReadOnlyField(elx));
		});
	};

	$(document).ready(process);

})();


(function() {

	var AbstractField = function(elm, tmpl) {
		
		if( !(this instanceof AbstractField) ) {
			return new AbstractField(elm);
		}

		this.elm = elm;
		this.options = {};
		this.uri = new csweb.URI();

		if( (elm === undefined) || (tmpl === undefined) ) {
			return;
		}

		this._prepareOptions();

		if( this._prepareURI() ) {
			return;
		}

		this._prepareElement(tmpl);

		this._prepareListeners();
	};

	cswui.AbstractField = AbstractField;

	AbstractField.template = '<span style="color:red;">{{message}}</span>';


	AbstractField.prototype._prepareOptions = function() {
		var self = this;
		$(this.elm).find('div').each(function(idx, elx) {
			var name = $(elx).attr('name');
			if( (name !== undefined) && (typeof name === 'string') ) {
				self.options[name.toLowerCase()] = $(elx).text();
			}
		});
	};

	AbstractField.prototype._prepareURI = function() {
		
		var opt,val;

		this.uri.scheme = cswui.defaultDeviceProtocol;

		if( !('device' in this.options) ) {
			$(this.elm).html(AbstractField.template);
			return true;
		}

		this.uri.path = this.options['device'];


		if( 'protocol' in this.options ) {
			this.uri.scheme = this.options['protocol'];
		}

		if( 'rate' in this.options ) {

			opt = 'rate';
			val = Number(this.options[opt]);

			if( isNaN(val) ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "rate" option must have a numeric value.'));
				return true;
			}

			if( val <= 0 ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "rate" option must have value > 0.'));
				return true;
			}

			this.options[opt] = val;
			this.uri.query[opt] = val;

		} else if( 'ratelimit' in this.options) {

			opt = 'ratelimit';
			val = Number(this.options[opt]);

			if( isNaN(val) ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "ratelimit" option must have a numeric value.'));
				return true;
			}

			if( val <= 0 ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "ratelimit" option must have value > 0.'));
				return true;
			}

			this.options[opt] = val;
			this.uri.query[opt] = val;
		}

		if( 'buffer' in this.options ) {

			opt = 'buffer';
			val = Number(this.options[opt]);

			if( isNaN(val) ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "buffer" option must have a numeric value.'));
				return true;
			}

			if( val <= 0 ) {
				$(this.elm).html(AbstractField.template.replace('{{message}}',
					'The "buffer" option must have value > 0.'));
				return true;
			}

			this.options[opt] = val;
			this.uri.query[opt] = val;
		}

		return false;
	};

	AbstractField.prototype._prepareElement = function(tmpl) {
		$(this.elm).html(tmpl);
	};

	AbstractField.prototype._prepareListeners = function() {

		var self = this;
		//
		// The order of the following section is important
		// because the 'open' event may occur during either
		// the call to _socketOnClose() or _socketOnOpen().
		//
		if( cswui.socket.readyState !== csweb.Socket.OPEN ) {
			this._socketOnClose();
		} 

		cswui.socket.addEventListener("open", function(event) {
			self._socketOnOpen(event);
		});

		cswui.socket.addEventListener(this.uri.toString(), function(event) {
			self._socketOnData(event);
		});

		cswui.socket.addEventListener("close", function(event) {
			self._socketOnClose();
		});

		if( cswui.socket.readyState === csweb.Socket.OPEN ) {
			this._socketOnOpen();
		} 
	};

	AbstractField.prototype._socketOnOpen = function(event) {
		cswui.socket.subscribe(this.uri);
		this.opened();
	};

	AbstractField.prototype._socketOnClose = function(event) {
		this.closed();
	};

	AbstractField.prototype._socketOnData = function(event) {
		if( (event.data !== undefined) && (typeof event.data === 'object') ) {
			var data = event.data;
			if( data.connected !== undefined ) {
				if( data.connected ) {
					this.connected();
				} else {
					this.disconnected();
				}
			}
		}
	};

	AbstractField.prototype.opened = function() {
		$(this.elm).find('.csw-status.csw-socket-closed').first().removeClass('csw-socket-closed');
	};

	AbstractField.prototype.closed = function() {
		$(this.elm).find('.csw-status').first().addClass('csw-socket-closed');
	};

	AbstractField.prototype.connected = function() {
		$(this.elm).find('.csw-status.csw-device-disconnected').first().removeClass('csw-device-disconnected');
	};

	AbstractField.prototype.disconnected = function() {
		$(this.elm).find('.csw-status').first().addClass('csw-device-disconnected');
	};

})();



(function() {


	var ReadOnlyField = function(elm) {

		if( !(this instanceof ReadOnlyField) ) {
			return new ReadOnlyField(elm);
		}

		this.superclass(elm, ReadOnlyField.template);
	};

	cswui.ReadOnlyField = ReadOnlyField;

	ReadOnlyField.template = '<div>' + 
								'<span class="csw-status"/>' + 
								'<span>&nbsp;</span>' + 
								'<span class="csw-value"/>' + 
								'<span>&nbsp;</span>' + 
								'<span class="csw-units"/>' +
							'</div>'


	ReadOnlyField.prototype = new cswui.AbstractField();
	ReadOnlyField.prototype.superclass = cswui.AbstractField;
	ReadOnlyField.prototype.constructor = ReadOnlyField;
	

	ReadOnlyField.prototype._socketOnData = function(event) {
		cswui.AbstractField.prototype._socketOnData.call(this, event);
		if( (event.data !== undefined) && (typeof event.data === 'object') ) {
			var data = event.data;
			if( (data.precision !== undefined) && (typeof data.precision === 'number') ) {
				data.value *= Math.pow(10,data.precision);
				data.value  = Math.round(data.value);
				data.value /= Math.pow(10,data.precision);
			}

			var e = $(this.elm).find('.csw-value').get(0);
			$(e).html(data.value);

			if( (data.units !== undefined) && (typeof data.units === 'string') ) {
				var e = $(this.elm).find('.csw-units').get(0);
				$(e).html(data.units);
			}
		}
	};

})();


(function() {


	var StripChartField = function(elm) {

		if( !(this instanceof StripChartField) ) {
			return new StripChartField(elm);
		}

		this.dygraph = null;
		this.chartdata = [];
		this.superclass(elm, StripChartField.template);
	};

	cswui.StripChartField = StripChartField;

	StripChartField.template = '<div class="csw-dygraph"/>' + 
								'<div class="csw-status"/>'

	StripChartField.defaultMaxChartSize = 10000;


	StripChartField.prototype = new cswui.AbstractField();
	StripChartField.prototype.superclass = cswui.AbstractField;
	StripChartField.prototype.constructor = StripChartField;

	
	StripChartField.prototype._prepareElement = function(tmpl) {
		cswui.AbstractField.prototype._prepareElement.call(this, tmpl);
		var e = $(this.elm).find('.csw-dygraph').get(0);
		this.dygraph = new Dygraph(e);
	};

	StripChartField.prototype._socketOnData = function(event) {
		cswui.AbstractField.prototype._socketOnData.call(this, event);
		if( (event.data !== undefined) && (typeof event.data === 'object') ) {
			var data = event.data;			
			if( data.length !== undefined ) {
				for(var idx=0; idx<data.length; idx++) {
					this.chartdata.push([new Date(data[idx].timestamp * 1000),data[idx].value]);
					if(this.chartdata.length > this._getMaxChartSize() ) {
						this.chartdata.shift();
					}
				}
			} else {
				this.chartdata.push([new Date(data.timestamp * 1000),data.value]);
				if(this.chartdata.length > this._getMaxChartSize() ) {
					this.chartdata.shift();
				}
			}
			this.dygraph.updateOptions({file:this.chartdata});

			if(data.units) {
				this.dygraph.updateOptions({ylabel:this.options.device + ' [' + data.units + ']','yAxisLabelWidth':75, xAxisLabelWidth:75});
			}
		}
	};
	
	StripChartField.prototype._getMaxChartSize = function() {
		if( this.options.buffer === undefined ) {
			return StripChartField.defaultMaxChartSize;
		}
		if( typeof this.options.buffer !== 'number') {
			return StripChartField.defaultMaxChartSize;
		}
		if( this.options.buffer <= 0 ) {
			return StripChartField.defaultMaxChartSize;
		}
		return this.options.buffer;
	};

})();
