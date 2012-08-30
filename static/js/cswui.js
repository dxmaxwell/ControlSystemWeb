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

	$(elm).html(cswui.ReadOnlyFieldTemplate);

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
			e.value = jmsg.value;

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


cswui.ReadOnlyFieldTemplate = 
	'<div style="clear:both;">' + 
		'<div class="csw-three-left csw-status"></div>' + 
		'<div class="csw-three-middle">' + 
			'<input name="value" class="csw-value" readonly="readonly" size="10"/>' +
		'</div>' + 
		'<div class="csw-three-right csw-units"></div>' +
	'</div>';


/* Lastly, setup document ready callback. */
$(document).ready(cswui.processDocument);
