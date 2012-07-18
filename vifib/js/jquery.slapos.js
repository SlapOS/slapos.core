(function ($) {
    'use strict';
    var methods = {
        init: function (options) {
            return this.each(function () {
                var settings = $.extend({
                    storage: 'localstorage'
                }, options),
                    setting;
                methods.store = settings.storage === 'localstorage' ? methods.lStore : methods.cStore;
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
        appid: function (value) {
            return $(this).slapos('store', 'appid', value);
        },

        deleteStore: function (name) {
            delete window.localStorage[name];
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
                document.cookie = name + '=' + value + ';domain=' + window.location.hostname + ';path=' + window.location.pathname;
            } else {
                var i, x, y, cookies = document.cookie.split(';');
                for (i = 0; i < cookies.length; i += 1) {
                    x = cookies[i].substr(0, cookies[i].indexOf('='));
                    y = cookies[i].substr(cookies[i].indexOf('=') + 1);
                    x = x.replace(/^\s+|\s+$/g, '');
                    if (x === name) {
                        return unescape(y);
                    }
                }
            }
        },

        statusDefault: function () {
            return {
                0: function () { console.error('status error code: 0'); },
                404: function () { console.error('status error code: Not Found !'); },
                500: function () { console.error('Server error !'); }
            };
        },

        request: function (type, method, args) {
            var statusCode, data;
            if (args.hasOwnProperty('statusCode')) {
                statusCode = args.statusCode || methods.statusDefault();
            } else {
                statusCode = methods.statusDefault();
            }
            if (args.hasOwnProperty('data')) {
                data = args.data || undefined;
            } else {
                data = undefined;
            }
            delete args.data;
            $.extend(args, {statusCode: statusCode});
              var ajaxOptions = {
                  type: type,
                  url: $(this).slapos('host') + method,
                  contentType: 'application/json',
                  data: JSON.stringify(data),
                  datatype: 'json',
                  context: $(this),
                  headers: {
                      'Accept': 'application/json',
                  },
                  beforeSend: function (xhr) {
                      if ($(this).slapos('access_token')) {
                          xhr.setRequestHeader('Authorization', $(this).slapos('store', 'token_type') + ' ' + $(this).slapos('access_token'));
                      }
                  }
              };
              $.extend(ajaxOptions, args);
              return $.ajax(ajaxOptions);
        },

        instanceList: function (args) {
            return $(this).slapos('request', 'GET', '/instance', args);
        },

        instanceInfo: function (url, args) {
            $.extend(args, {url: url});
            return $(this).slapos('request', 'GET', '', args);
        },

        instanceRequest: function (args) {
            return $(this).slapos('request', 'POST', '/instance', args);
        },
        
        instanceBang: function (url, args) {
            $.extend(args, {url: url + '/bang'});
            return $(this).slapos('request', 'POST', '', args);
        },

        instanceCertificate: function (url, args) {
            $.extend(args, {url: url + '/certificate'});
            return $(this).slapos('request', 'GET', '', args);
        },

        //softwareList: function (args) {
            //return $(this).slapos('request', '', args);
        //},

        //softwareInfo: function (url, args) {
            //return $(this).slapos('request', '', args);
        //},
        
        //computerList: function (args) {
            //return $(this).slapos('request', '', args);
        //},

        computerInfo: function (url, args) {
            $.extend(args, {url: url});
            return $(this).slapos('request', 'GET', '', args);
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
