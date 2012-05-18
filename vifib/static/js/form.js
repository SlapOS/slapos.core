/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */
(function($) {
	var routes = {
		"/instance" : "requestInstance",
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

	var getDate = function () {
		var today = new Date();
		return [today.getFullYear(), today.getMonth(), today.getDay()].join('/')
			+ ' ' + [today.getHours(), today.getMinutes(), today.getSeconds()].join(':');
	};

	var substractLists = function(l1, l2){
		var newList = [];
		$.each(l2, function(){
			if ($.inArray(""+this, l1) == -1) {
				newList.push(""+this);
			}
		});
		return newList;
	};
	
	var redirect = function(){
		$(this).vifib('render', 'auth', {
			'host':'http://10.8.2.34:12002/erp5/web_site_module/hosting/request-access-token',
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
			$(this).slapos();
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

		extractInstanceURIFromUrl: function () {
			return decodeURIComponent($(this).attr('href').split('/').pop())
		},

		authenticate: function(data) {
			for (var d in data) {
				if (data.hasOwnProperty(d)) {
					$(this).slapos('store', d, data[d]);
				}
			}
		},

		refresh: function(method, interval, eventName){
			eventName = eventName || 'ajaxStop';
			var $this = $(this);
			$(this).one(eventName, function(){
				var id = setInterval(function(){
					method.call($this);
				}, interval * 1000);
				$.subscribe('urlChange', function(e, d){
					clearInterval(id);
				})
			});
		},

		showInstance: function (uri) {
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError
			};
			$(this).slapos('instanceInfo', uri, {
				success: function(infos){
					$(this).vifib('render', 'instance', infos);
				},
				statusCode: statusCode
			});
		},

		getCurrentList: function () {
			var list = [];
			$.each($(this).find('a'), function () {
				list.push($(this).vifib('extractInstanceURIFromUrl'));
			});
			return list;
		},

		listComputers: function(){
			$(this).vifib('render', 'server.list');
		},
		
		refreshRowInstance: function(){
			return this.each(function(){
				var url = $(this).find('a').vifib('extractInstanceURIFromUrl');
				$(this).vifib('fillRowInstance', url);
			});
		},

		fillRowInstance: function(url){
			return this.each(function(){
				$(this).slapos('instanceInfo', url, {
					success: function(instance){
						$.extend(instance, {'url': methods.genInstanceUrl(url)});
						$(this).vifib('render', 'instance.list.elem', instance);
					}
				});
			});
		},
		
		refreshListInstance: function () {
			var currentList = $(this).vifib('getCurrentList');
			$(this).slapos('instanceList', {
				success: function (data) {
					var $this = $(this);
					var newList = substractLists(currentList, data['list']);
					var oldList = substractLists(data['list'], currentList);
					$.each(newList, function(){
						var url = this+"";
						var row = $("<tr></tr>").vifib('fillRowInstance', url);
						$this.prepend(row);
					});
					console.log("newList")
					console.log(newList)
					console.log("oldList")
					console.log(oldList)
				},
			});
		},

		listInstances: function(){
			var $this = $(this);
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError,
				503: serverError
			};
			var table = $(this).vifib('render', 'instance.list').find("#instance-table");
			table.vifib('refresh', methods.refreshListInstance, 30);
			$(this).slapos('instanceList', {
				success: function(data){
					$.each(data['list'], function(){
						var url = this+"";
						var row = $("<tr></tr>").vifib('fillRowInstance', url);
						row.vifib('refresh', methods.refreshRowInstance, 30);
						table.append(row);
					});
				}, statusCode: statusCode});
		},
		
		listInvoices: function(){
			$(this).vifib('render', 'invoice.list');
		},

		instanceInfo: function (url, callback) {
			$(this).slapos('instanceInfo', {
				success: callback, url: url
			});
		},

		requestInstance: function() {
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
			var statusCode = {
				401: redirect,
				402: payment,
				404: notFound,
				500: serverError
			};
			var instance = {
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
			$.extend(instance, data);
			var args = {
				statusCode: statusCode,
				data: instance,
				success: function (response) {
					console.log(response);
				}
			};
			return this.each(function(){
				$(this).slapos('instanceRequest', args);
			});
		},

		popup: function(message, state) {
			state = state || 'error';
			return this.each(function(){
				$(this).prepend(ich['error'](
						{'message': message, 'state': state, 'date': getDate()}
						, true))
			})
		},

		render: function(template, data){
			return this.each(function(){
				$(this).html(ich[template](data, true));
			});
		},

		renderAppend: function(template, data){
			$(this).append(ich[template](data, true));
		},

		renderPrepend: function(template, data){
			$(this).prepend(ich[template](data, true));
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
