/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */
(function ($) {
    'use strict';
    var routes = {
        '/instance' : 'requestInstance',
        '/instance/:url' : 'showInstance',
        '/instance/:url/bang' : 'showBangInstance',
        '/computers' : 'listComputers',
        '/instances' : 'listInstances',
        '/invoices' : 'listInvoices'
    },
        router = function (e, d) {
            var $this = $(this);
            $.each(routes, function (pattern, callback) {
                pattern = pattern.replace(/:\w+/g, '([^\/]+)');
                var regex = new RegExp('^' + pattern + '$'),
                    result = regex.exec(d);
                if (result) {
                    result.shift();
                    methods[callback].apply($this, result);
                }
            });
        },

        /* Based on ben alman code
         * https://raw.github.com/cowboy/jquery-misc/master/jquery.ba-serializeobject.js
         */
        serializeObject = function () {
            var obj = {};
            $.each($(this).serializeArray(), function (i, o) {
                var k = o.name,
                    v = o.value;
                obj[k] = obj[k] === undefined ? v
                    : $.isArray(obj[k]) ? obj[k].concat(v)
                    : [obj[k], v];
            });
            return obj;
        },

        getDate = function () {
            var today = new Date();
            return [today.getFullYear(), today.getMonth(), today.getDay()].join('/') +
                ' ' + [today.getHours(), today.getMinutes(), today.getSeconds()].join(':');
        },

        substractLists = function (l1, l2) {
            var newList = [];
            $.each(l2, function () {
                if ($.inArray(this.toString(), l1) === -1) {
                    newList.push(this.toString());
                }
            });
            return newList;
        },

        redirect = function () {
            $(this).vifib('render', 'auth', {
                'host': 'http://10.8.2.34:12006/erp5/web_site_module/hosting/request-access-token',
                'client_id': 'client',
                'redirect': escape(window.location.href)
            });
        },

        payment = function (jqxhr) {
            var message = $.parseJSON(jqxhr.responseText).error;
            $(this).vifib('popup', message, 'information');
        },

        notFound = function (jqxhr) {
            var message = $.parseJSON(jqxhr.responseText).error;
            $(this).vifib('popup', message);
        },

        serverError = function (jqxhr) {
            var message = jqxhr.responseText;
            if (typeof message == 'object') {
                message = $.parseJSON(jqxhr.responseText).error;
            }
            $(this).vifib('popup', message);
        },

        bad_request = function (jqxhr) {
            var message = jqxhr.responseText;
            if (typeof message == 'object') {
                message = $.parseJSON(jqxhr.responseText).error;
            }
            $(this).vifib('popup', message);
        },
        
        spinOptions = {color:  '#FFF', lines: 9, length: 3, width: 2, radius: 6, rotate: 0, trail: 36, speed: 1.0},
        
        methods = {
            init: function () {
                // Initialize slapos in this context
                $(this).slapos();
                var $this = $(this);
                // Bind Loading content
                $('#loading').ajaxStart(function () {
                    $(this).spin(spinOptions);
                }).ajaxStop(function () {
                    $(this).spin(false);
                });
                // Bind to urlChange event
                return this.each(function () {
                    $.subscribe('urlChange', function (e, d) {
                        router.call($this, e, d);
                    });
                    $.subscribe('auth', function (e, d) {
                        $(this).vifib('authenticate', d);
                    });
                });
            },

            genInstanceUrl: function (uri) {
                return $.genHash(['instance', encodeURIComponent(uri)]);
            },

            extractInstanceURIFromHref: function () {
                return decodeURIComponent($(this).attr('href').split('/').pop());
            },
            
            extractInstanceURIFromHashtag: function () {
                var loc = window.location.hash.split('/'),
                    i = $.inArray("instance", loc);
                return (i !== -1 && loc.length > i) ? decodeURIComponent(loc[i + 1]) : "";
            },

            genBangUrl: function (uri) {
                return $.genHash(["instance", encodeURIComponent(uri), "bang"]);
            },

            authenticate: function (data) {
                var d;
                for (d in data) {
                    if (data.hasOwnProperty(d)) {
                        $(this).slapos('store', d, data[d]);
                    }
                }
            },

            refresh: function (method, interval, eventName) {
                eventName = eventName || 'ajaxStop';
                var $this = $(this);
                $(this).one(eventName, function () {
                    var id = setInterval(function () {
                        method.call($this);
                    }, interval * 1000);
                    $.subscribe('urlChange', function (e, d) {
                        clearInterval(id);
                    });
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
                    success: function (infos) {
                        infos.status = $(this).vifib('getRender', 'instance.' + infos.status);
                        infos.actions = [
                            {name: "Bang", url: methods.genBangUrl(decodeURIComponent(uri))}
                        ];
                        $(this).vifib('render', 'instance', infos);
                        var form = $(this).find("#instance-form");
                        form.vifib('prepareForm');
                    },
                    statusCode: statusCode
                });
            },

            bindStopStartButtons: function() {
                $("#startInstance").click($.proxy(methods.startInstance, $(this)));
                $("#stopInstance").click($.proxy(methods.stopInstance, $(this)));
            },

            prepareForm: function () {
                $(this).vifib('bindStopStartButtons');
                $("#bangInstance").click();
                $(this).vifib('refresh', methods.refreshInstanceForm, 30); 
            },

            refreshInstanceForm: function () {
                return this.each(function () {
                    var uri = $(this).vifib("extractInstanceURIFromHashtag");
                    $(this).slapos('instanceInfo', uri, {
                        success: function (data) {
                            var status = $(this).vifib('getRender', 'instance.' + data.status)
                            $("[name=software_type]").val(data.software_type);
                            $("#instanceStatus").html(status);
                            $(this).vifib('bindStopStartButtons');
                        }
                    });
                });
            },

            stopInstance: function() {
                $(this).vifib('changeStatusInstance', 'stopped');
                return false;
            },

            startInstance: function() {
                $(this).vifib('changeStatusInstance', 'started');
                return false;
            },

            showBangInstance: function () {
                var statusCode = {
                    400: bad_request,
                    401: redirect,
                    402: payment,
                    404: notFound,
                    500: serverError,
                };
                return this.each(function () {
                    $(this).vifib("render", 'form.bang.instance');
                    $(this).find("#form-bang").submit(function () {
                        var data = $(this).serializeObject(),
                            uri = methods.extractInstanceURIFromHashtag();
                        $(this).slapos('instanceBang', uri, {
                            data: data,
                            statusCode: statusCode,
                            success: function () {
                                $.redirect(['instance', encodeURIComponent(uri)]);
                            }
                        });
                        return false;
                    });
                });
            },

            changeStatusInstance: function (status) {
                var uri = methods.extractInstanceURIFromHashtag(),
                    data = $(this).vifib('extractInstanceInfo');
                data.status = status;
                $(this).vifib('requestAsking', data, function (){
                    $(this).vifib('refreshInstanceForm');
                });
            },

            getCurrentList: function () {
                var list = [];
                $.each($(this).find('a'), function () {
                    list.push($(this).vifib('extractInstanceURIFromHref'));
                });
                return list;
            },

            listComputers: function () {
                $(this).vifib('render', 'server.list');
            },
            
            refreshRowInstance: function () {
                return this.each(function () {
                    var url = $(this).find('a').vifib('extractInstanceURIFromHref');
                    $(this).vifib('fillRowInstance', url);
                });
            },

            fillRowInstance: function (url) {
                return this.each(function () {
                    $(this).slapos('instanceInfo', url, {
                        success: function (instance) {
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
                        var $this = $(this),
                            newList = substractLists(currentList, data.list),
                            oldList = substractLists(data.list, currentList);
                        $.each(newList, function () {
                            var url = this.toString(),
                                row = $('<tr></tr>').vifib('fillRowInstance', url);
                            $this.prepend(row);
                        });
                    }
                });
            },

            listInstances: function () {
                var $this = $(this),
                    statusCode = {
                        401: redirect,
                        402: payment,
                        404: notFound,
                        500: serverError,
                        503: serverError
                    },
                    table = $(this).vifib('render', 'instance.list').find('#instance-table');
                table.vifib('refresh', methods.refreshListInstance, 30);
                $(this).slapos('instanceList', {
                    success: function (data) {
                        $.each(data.list, function () {
                            var url = this.toString(),
                                row = $('<tr></tr>').vifib('fillRowInstance', url);
                            row.vifib('refresh', methods.refreshRowInstance, 30);
                            table.append(row);
                        });
                    },
                    statusCode: statusCode
                });
            },
            
            listInvoices: function () {
                $(this).vifib('render', 'invoice.list');
            },

            instanceInfo: function (url, callback) {
                $(this).slapos('instanceInfo', {
                    success: callback,
                    url: url
                });
            },

            requestInstance: function () {
                $(this).vifib('render', 'form.new.instance');
                $(this).find('form').submit(function () {
                    var data = $(this).vifib('extractInstanceInfo');
                    $(this).vifib('requestAsking', data);
                    return false;
                });
            },

            extractInstanceInfo: function () {
                var data = {};
                $(this).find('input').serializeArray().map(function (elem) {
                    data[elem.name] = elem.value;
                });
                return data;
            },

            requestAsking: function (data, callback) {
                var statusCode = {
                    400: bad_request,
                    401: redirect,
                    402: payment,
                    404: notFound,
                    500: serverError
                },
                    instance = {
                        software_type: 'type_provided_by_the_software',
                        slave: false,
                        status: 'started',
                        parameter: {
                            Custom1: 'one string',
                            Custom2: 'one float',
                            Custom3: ['abc', 'def']
                        },
                        sla: {
                            computer_id: 'COMP-0'
                        }
                    },
                    args = {
                        statusCode: statusCode,
                        data: instance,
                        success: callback
                    };
                $.extend(instance, data);
                instance.software_release = "testVifibSlaposRestAPIV1.TestVifibSlaposRestAPIV1.test_instance_destruction_started0.648835385933";
                $(this).slapos('instanceRequest', args);
            },

            popup: function (message, state) {
                state = state || 'error';
                return this.each(function () {
                    $(this).prepend(ich.error({
                        'message': message,
                        'state': state,
                        'date': getDate()
                    }, true));
                });
            },

            render: function (template, data) {
                return this.each(function () {
                    $(this).html(ich[template](data, true));
                });
            },
            
            getRender: function (template, data) {
                return ich[template](data, true);
            },

            renderAppend: function (template, data) {
                $(this).append(ich[template](data, true));
            },

            renderPrepend: function (template, data) {
                $(this).prepend(ich[template](data, true));
            }
        };

    $.fn.vifib = function (method) {
        if (methods[method]) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.vifib' );
        }
    };

    /* Thanks to Ben Alman
     * https://raw.github.com/cowboy/jquery-misc/master/jquery.ba-serializeobject.js
     */
    $.fn.serializeObject = function(){
        var obj = {};
            $.each( this.serializeArray(), function(i,o){
                var n = o.name,
                    v = o.value;
                obj[n] = obj[n] === undefined ? v
                  : $.isArray( obj[n] ) ? obj[n].concat( v )
                  : [ obj[n], v ];
            });
        return obj;
    }; 
})(jQuery);

$('#main').vifib();
