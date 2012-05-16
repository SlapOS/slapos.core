(function ($) {
	"use strict";
	var methods = {
		init: function (options) {
			var settings = $.extend({
			}, options);

			return this.each(function () {
				var setting;
				methods.store = Modernizr.localstorage ? methods.lStore : methods.cStore;
				for (setting in settings) {
					if (settings.hasOwnProperty(setting)) {
						$(this).slapos('store', setting, settings[setting]);
					}
				}
			});
		},

		/* Getters & Setters shortcuts */
		access_token: function (value) {
			return $(this).slapos('store', 'access_token', value);
		},
		host: function (value) {
			return $(this).slapos('store', 'host', value);
		},
		clientID: function (value) {
			return $(this).slapos('store', 'clientID', value);
		},

		/* Local storage method */
		lStore: function (name, value) {
			if (Modernizr.localstorage) {
				return value === undefined ? window.localStorage[name] : window.localStorage[name] = value;
			}
			return false;
		},

		/* Cookie storage method */
		cStore: function (name, value) {
			if (value !== undefined) {
				document.cookie = name + "=" + value + ";domain=" + window.location.hostname + ";path=" + window.location.pathname;
			} else {
				var i, x, y, cookies = document.cookie.split(';');
				for (i = 0; i < cookies.length; i += 1) {
					x = cookies[i].substr(0, cookies[i].indexOf('='));
					y = cookies[i].substr(cookies[i].indexOf('=') + 1);
					x = x.replace(/^\s+|\s+$/g, "");
					if (x === name) {
						return unescape(y);
					}
				}
			}
		},

		statusDefault: function () {
			return {
				0: function () { console.error("status error code: 0"); },
				404: function () { console.error("status error code: Not Found !"); },
				500: function () { console.error("Server error !"); }
			};
		},

		request: function (type, url, authentication, callback, statusCode, data) {
			return this.each(function () {
				$.ajax({
					url: url,
					type: type,
					contentType: 'application/json',
					data: JSON.stringify(data),
					dataType: 'json',
					context: $(this),
					beforeSend: function (xhr) {
						if ($(this).slapos("access_token") && authentication) {
							xhr.setRequestHeader("Authorization", $(this).slapos("store", "token_type") + " " + $(this).slapos("access_token"));
							xhr.setRequestHeader("Accept", "application/json");
						}
					},
					statusCode: statusCode,
					success: callback
				});
			});
		},

		prepareRequest: function (methodName, callback, statusCode, url, data) {
			data = data || undefined;
			statusCode = statusCode || methods.statusDefault();
			var $this = $(this);
			return this.each(function(){
				$(this).slapos('discovery', function(access){
					if (access.hasOwnProperty(methodName)) {
						url = url || access[methodName].url;
						$this.slapos('request',
							access[methodName].method,
							url,
							access[methodName].authentication,
							callback,
							statusCode,
							data);
					}
				});
			})
		},

		discovery: function (callback) {
			return this.each(function(){
				$.ajax({
					url: "http://192.168.242.64:12002/erp5/portal_vifib_rest_api_v1",
					dataType: "json",
					beforeSend: function (xhr) {
						xhr.setRequestHeader("Accept", "application/json");
					},
					success: callback
				});
			});
		},

		instanceList: function (callback, statusCode) {
			return $(this).slapos('prepareRequest', 'instance_list', callback, statusCode);
		},

		instanceInfo: function (url, callback, statusCode) {
			url = decodeURIComponent(url);
			return $(this).slapos('prepareRequest', 'instance_info', callback, statusCode, url);
		}

	};

	$.fn.slapos = function (method) {
		if (methods[method]) {
			return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
		} else if (typeof method === 'object' || !method) {
			return methods.init.apply(this, arguments);
		} else {
			$.error('Method ' +  method + ' does not exist on jQuery.slapos');
		}
	};
}(jQuery));
