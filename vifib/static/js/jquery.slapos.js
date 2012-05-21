(function ($) {
    'use strict';
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

        request: function (type, authentication, args) {
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
            return this.each(function () {
                var ajaxOptions = {
                    type: type,
                    contentType: 'application/json',
                    data: JSON.stringify(data),
                    datatype: 'json',
                    context: $(this),
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('REMOTE_USER', 'test_vifib_customer');
                        xhr.setRequestHeader('Accept', 'application/json');
                        if ($(this).slapos('access_token') && authentication) {
                            //xhr.setRequestHeader('Authorization', $(this).slapos('store', 'token_type') + ' ' + $(this).slapos('access_token'));
                            //xhr.setRequestHeader('Accept', 'application/json');
                        }
                    }
                };
                $.extend(ajaxOptions, args);
                $.ajax(ajaxOptions);
            });
        },

        prepareRequest: function (methodName, args) {
            var $this = $(this);
            args = args || {};
            return this.each(function () {
                $(this).slapos('discovery', function (access) {
                    if (access.hasOwnProperty(methodName)) {
                        var url = args.url || access[methodName].url;
                        $.extend(args, {'url': url});
                        $this.slapos('request',
                            access[methodName].method,
                            access[methodName].authentication,
                            args);
                    }
                });
            });
        },

        discovery: function (callback) {
            return this.each(function () {
                $.ajax({
                    url: 'http://10.8.2.34:12006/erp5/portal_vifib_rest_api_v1',
                    dataType: 'json',
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('Accept', 'application/json');
                    },
                    success: callback
                });
            });
        },

        instanceList: function (args) {
            return $(this).slapos('prepareRequest', 'instance_list', args);
        },

        instanceInfo: function (url, args) {
            url = decodeURIComponent(url);
            $.extend(args, {'url': url});
            return $(this).slapos('prepareRequest', 'instance_info', args);
        },

        instanceRequest: function (args) {
            return $(this).slapos('prepareRequest', 'request_instance', args);
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
