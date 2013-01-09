/*
 * Control System Web User Interface.
 */

var cswui = {};

/*
 * Process document for 'csw' elements. Typically called only once when docuemnt is 'ready'.
 */
cswui.processDocument = function() {	
	cswui.ws = new csweb.WebSocket('ws://'+location.host+'/device/ws');
	$('.csw-readonly-field').each(function(idx, elx) {
		cswui.processReadOnlyField(elx);
	});
	$('.csw-strip-chart').each(function(idx, elx) {
		cswui.processStripChart(elx);
	});
};


cswui.processGeneralField = function(elm) {

	if(!elm.csw) {
		elm.csw = {};
	}

	$(elm).find('div[name=device]').each(function(idx, elx) {
		elm.csw.device = $(elx).text();
		$(elx).remove()
	});
}


cswui.processReadOnlyField = function(elm) {
	
	cswui.processGeneralField(elm);
	
	elm.csw.deviceURI = elm.csw.device;

	$(elm).html(cswui.templates.readOnlyField);

	$(elm).find('.csw-status').first().addClass('csw-ws-disconnected');


	if(cswui.ws.readyState == csweb.WebSocket.OPEN) {
		console.log("Ready State is OPEN");
		cswui.ws.subscribe(elm.csw.deviceURI);
	}

	$(cswui.ws).on("open", function(event) { 
		cswui.ws.subscribe(elm.csw.deviceURI);
		$(elm).find('.csw-status').first().removeClass('csw-ws-disconnected');
	});
	
	$(cswui.ws).on("message", function(event) {
		var jmsg = JSON.parse(event.message);
		if(jmsg && jmsg[elm.csw.deviceURI]) {
			jmsg = jmsg[elm.csw.deviceURI];
			if(jmsg.precision !== null) {
				jmsg.value *= Math.pow(10,jmsg.precision);
				jmsg.value  = Math.round(jmsg.value);
				jmsg.value /= Math.pow(10,jmsg.precision);
			}
			var e = $(elm).find('.csw-value').get(0);
			$(e).html(jmsg.value);

			if(jmsg.units !== null) {
				var e = $(elm).find('.csw-units').get(0);
				$(e).html(jmsg.units);
			}
		}
	});
	
	$(cswui.ws).on("error", function(event) {
		//alert("Got Error!");
	});
	
	$(cswui.ws).on("close", function(event) {
		$(elm).find('.csw-status').first().addClass('csw-ws-disconnected');
	});
};

cswui.processStripChart = function(elm) {

	cswui.processGeneralField(elm);

	$(elm).find('div[name=buffer]').each(function(idx, elx) {
		elm.csw.buffer = $(elx).text();
		$(elx).remove()
	});
	
	elm.csw.deviceURI = elm.csw.device;

	if(elm.csw.buffer) {
		elm.csw.deviceURI += '?buffer=' + elm.csw.buffer;
	}

	$(elm).html(cswui.templates.stripChart);

	var e = $(elm).find('.csw-dygraph').get(0);

	elm.csw.dygraph = new Dygraph(e);
	elm.csw.chartdata = [];

	if(cswui.ws.readyState == csweb.WebSocket.OPEN) {
		console.log("Ready State is OPEN");
		cswui.ws.subscribe(elm.csw.deviceURI);
	}

	$(cswui.ws).on("open", function(event) { 
		cswui.ws.subscribe(elm.csw.deviceURI);
		$(elm).find('.csw-status').first().removeClass('csw-ws-disconnected');
	});
	
	$(cswui.ws).on("message", function(event) {
		var jmsg = JSON.parse(event.message);
		if(jmsg && jmsg[elm.csw.deviceURI]) {
			jmsg = jmsg[elm.csw.deviceURI];
			//if(jmsg.precision !== null) {
			//	jmsg.value *= Math.pow(10,jmsg.precision);
			//	jmsg.value  = Math.round(jmsg.value);
			//	jmsg.value /= Math.pow(10,jmsg.precision);
			//}

			if($.isArray(jmsg)) {
				for(idx in jmsg) {
					elm.csw.chartdata.push([new Date(jmsg[idx].timestamp * 1000),jmsg[idx].value]);
					if(elm.csw.chartdata.length>elm.csw.buffer) {
						elm.csw.chartdata.shift();
					}
				}
			} else {
				elm.csw.chartdata.push([new Date(jmsg.timestamp * 1000),jmsg.value]);
				if(elm.csw.chartdata.length>elm.csw.buffer) {
					elm.csw.chartdata.shift();
				}
			}
			elm.csw.dygraph.updateOptions({file:elm.csw.chartdata});

			//var e = $(elm).find('.csw-value').get(0);
			//$(e).html(jmsg.value);

			//if(jmsg.units !== null) {
			//	var e = $(elm).find('.csw-units').get(0);
			//	$(e).html(jmsg.units);
			//}

			if(jmsg.units !== null) {
				elm.csw.dygraph.updateOptions({ylabel:elm.csw.device + ' [' + jmsg.units + ']','yAxisLabelWidth':75, xAxisLabelWidth:75});
			}
		}
	});

	$(cswui.ws).on("error", function(event) {
		//alert("Got Error!");
	});
	
	$(cswui.ws).on("close", function(event) {
		$(elm).find('.csw-status').first().addClass('csw-ws-disconnected');
	});
};

cswui.templates = {
	'readOnlyField':
		'<div>' + 
			'<span class="csw-status"/>' + 
			'<span>&nbsp;</span>' + 
			'<span class="csw-value"/>' + 
			'<span>&nbsp;</span>' + 
			'<span class="csw-units"/>' +
		'</div>',

	'stripChart':
		'<div class="csw-dygraph">' + '</div>' +
		'<div class="csw-status"/>'
};

/* Lastly, setup document ready callback. */
$(document).ready(cswui.processDocument);
