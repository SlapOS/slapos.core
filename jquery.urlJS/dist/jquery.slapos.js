/*! jQuery Slapos - v0.1.0 - 2012-05-11
* Copyright (c) 2012 Nexedi; Licensed  */

(function ($) {
	"use strict";
	var methods = {
		init: function (options) {
			var settings = $.extend({
				'host': '',
				'access_token': '',
				'clientID': ''
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
				404: function () { console.error("status error code: Not Found !"); }
			};
		},

		request: function (type, url, callback, statusCode, data) {
			data = data || '';
			statusCode = statusCode || this.statusDefault;
			return this.each(function () {
				$.ajax({
					url: $(this).slapos('host') + url,
					type: type,
					contentType: 'application/octet-stream',
					data: JSON.stringify(data),
					dataType: 'json',
					context: $(this),
					beforeSend: function (xhr) {
						if ($(this).slapos("access_token")) {
							xhr.setRequestHeader("Authorization", $(this).slapos("store", "token_type") + " " + $(this).slapos("access_token"));
							xhr.setRequestHeader("Accept", "application/json");
						}
					},
					statusCode: statusCode,
					success: callback
				});
			});
		},

		newInstance: function (data, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/request', callback, statusEvent, data);
		},

		deleteInstance: function (id, callback, statusEvent) {
			return $(this).slapos('request', 'DELETE', '/instance/' + id, callback, statusEvent);
		},

		getInstance: function (id, callback, statusEvent) {
			return $(this).slapos('request', 'GET', '/instance/' + id, callback, statusEvent);
		},

		getInstanceCert: function (id, callback, statusEvent) {
			return $(this).slapos('request', 'GET', '/instance/' + id + '/certificate', callback, statusEvent);
		},

		bangInstance: function (id, log, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/instance/' + id + '/bang', callback, statusEvent, log);
		},

		editInstance: function (id, data, callback, statusEvent) {
			return $(this).slapos('request', 'PUT', '/instance/' + id, callback, statusEvent, data);
		},

		newComputer: function (data, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/computer', callback, statusEvent, data);
		},

		getComputer: function (id, callback, statusEvent) {
			return $(this).slapos('request', 'GET', '/computer/' + id, callback, statusEvent);
		},

		editComputer: function (id, data, callback, statusEvent) {
			return $(this).slapos('request', 'PUT', '/computer/' + id, callback, statusEvent, data);
		},

		newSoftware: function (computerId, data, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/computer/' + computerId + '/supply', callback, statusEvent, data);
		},

		bangComputer: function (id, log, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/computer/' + id + '/bang', callback, statusEvent, log);
		},

		computerReport: function (id, data, callback, statusEvent) {
			return $(this).slapos('request', 'POST', '/computer/' + id + '/report', callback, statusEvent, data);
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
