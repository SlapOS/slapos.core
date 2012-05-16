/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */
(function($) {
	var routes = {
		"/instance" : "requestService",
		"/instance/:url" : "showInstance",
		"/computers" : "listComputers",
		"/instances" : "listInstances",
		"/invoices" : "listInvoices"
	}

	var router = function(e, d){
		var $this = $(this);
		$.each(routes, function(pattern, callback){
			pattern = pattern.replace(/:\w+/g, '([^\/]+)');
			var regex = new RegExp('^' + pattern + '$');
			var result = regex.exec(d);
			if (result) {
				result.shift();
				methods[callback].apply($this, result);
			}
		});
	}
	
	var redirect = function(){
		$(this).vifib('render', 'auth', {
			'host':'http://192.168.242.64:12002/erp5/web_site_module/hosting/request-access-token',
			'client_id': 'client',
			'redirect':escape(window.location.href)
		})
	};

	var payment = function(jqxhr){
		var message = $.parseJSON(jqXHR.responseText).error
		$(this).vifib('popup', message, "information");
	};

	var notFound = function(jqxhr){
		var message = $.parseJSON(jqXHR.responseText).error
		$(this).vifib('popup', message);
	};

	var serverError = function(jqxhr){
		var message = $.parseJSON(jqxhr.responseText).error
		$(this).vifib('popup', message);
	};

	var spinOptions = {color: "#FFF", lines:9, length:3, width:2, radius:6, rotate:0, trail:36, speed:1.0};

	var methods = {
		init: function() {
			// Initialize slapos in this context
			$(this).slapos({host: 'http://192.168.242.64:12002/erp5/portal_vifib_rest_api_v1'});
			var $this = $(this);
			// Bind Loading content
			$("#loading").ajaxStart(function(){
				$(this).spin(spinOptions);
			}).ajaxStop(function(){
				$(this).spin(false);
			});
			// Bind to urlChange event
			return this.each(function(){
				$.subscribe("urlChange", function(e, d){
					router.call($this, e, d);
				});
				$.subscribe("auth", function(e, d){
					$(this).vifib("authenticate", d);
				});
			});
		},

		genInstanceUrl: function(uri){
			return location.href.split('#')[0] + "#/instance/" + encodeURIComponent(uri)
		},

		authenticate: function(data) {
			for (var d in data) {
				if (data.hasOwnProperty(d)) {
					$(this).slapos('store', d, data[d]);
				}
			}
		},

		showInstance: function (uri) {
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError
			};
			var $this = $(this);
			$(this).slapos('instanceInfo', uri, function(infos){
					$this.vifib('render', 'instance', infos);
				}, statusCode);
		},

		listComputers: function(){
			$(this).vifib('render', 'server.list');
		},
		
		listInstances: function(){
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError
			};
			var $this = $(this);
			$(this).slapos('instanceList', function(data){
					$(this).vifib('render', 'service.list'),
					$.each(data['list'], function(){
						var url = this+"";
						$this.vifib('instanceInfo', url, function(instance){
							$.extend(instance, {'url': methods.genInstanceUrl(url)})
							$this.vifib('renderAppend', 'service.list.elem', 'service.table', instance);
						})
					})},
					statusCode
				);
		},
		
		listInvoices: function(){
			$(this).vifib('render', 'invoice.list');
		},

		instanceInfo: function (url, callback) {
			$(this).slapos('instanceInfo', url, callback);
		},

		requestService: function() {
			$(this).vifib('render', 'form.new.instance');
			var data = {};
			$(this).find("form").submit(function(){
				$(this).find('input').serializeArray().map(function(elem){
					data[elem["name"]] = elem["value"];
				});
				$(this).vifib('requestAsking', data);
				return false;
			});
		},

		requestAsking: function(data){
			var request = {
			  software_type: "type_provided_by_the_software",
			  slave: false,
			  status: "started",
			  parameter: {
				Custom1: "one string",
				Custom2: "one float",
				Custom3: ["abc", "def"],
				},
			  sla: {
				computer_id: "COMP-0",
				}
			};
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError
			};
			$.extend(request, data);
			$(this).slapos('newInstance', request, function(data){
					$(this).html(data);},
					statusCode
				);
		},

		popup: function(message, state) {
			state = state || 'error';
			return this.each(function(){
				$(this).prepend(ich['error']({'message': message, 'state': state}, true))
			})
		},

		render: function(template, data){
			$(this).html(ich[template](data, true));
		},

		renderAppend: function(template, rootId, data){
			rootId = rootId.replace('.', '\\.');
			$(this).find('#'+rootId).append(ich[template](data, true));
		}
	};

	$.fn.vifib = function(method){
		if ( methods[method] ) {
			return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
		} else if ( typeof method === 'object' || ! method ) {
			return methods.init.apply( this, arguments );
		} else {
			$.error( 'Method ' +  method + ' does not exist on jQuery.vifib' );
		}
	};
})(jQuery);

$("#main").vifib();
