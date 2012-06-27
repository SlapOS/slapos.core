/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */
(function ($) {
    'use strict';
    var getDate = function () {
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
            if (typeof message === 'object') {
                message = $.parseJSON(jqxhr.responseText).error;
            }
            $(this).vifib('popup', message);
        },

        bad_request = function (jqxhr) {
            var message = jqxhr.responseText;
            if (typeof message === 'object') {
                message = $.parseJSON(jqxhr.responseText).error;
            }
            $(this).vifib('popup', message);
        },

        spinOptions = {color: "#FFFFFF", lines: 30, length: 0, width: 5, radius: 7, rotate: 0, trail: 60, speed: 1.6},

        methods = {
            init: function () {
                return this.each(function () {
                    // JQM configuration
                    // Initialize slapos in this context
                    $(this).slapos({'host': 'http://10.8.2.34:12006/erp5/portal_vifib_rest_api_v1'});
                    $.router.routes.add('/page1', 0, methods.showPage1, $(this));
                    $.router.routes.add('/page2', 0, methods.showPage2, $(this));
                    $.router.routes.add('/', 0, methods.showRoot, $(this));
                });
            },

            showPage1: function (params) {
                return this.each(function () {
                    var page = methods.getRender('page1');
                    methods.changePage(page);
                });
            },
            
            showPage2: function (params) {
                return this.each(function () {
                    var page = methods.getRender('page2');
                    methods.changePage(page);
                });
            },

            changePage: function (page) {
                $('body').append(page);
                $.mobile.changePage(page, {changeHash: false, transition: 'slide'});
            },

            genInstanceUrl: function (uri) {
                return $.router.genHash(['instance', 'id', encodeURIComponent(uri)]);
            },
            
            genSoftwareUrl: function (uri) {
                return $.router.genHash(['library', 'software', encodeURIComponent(uri)]);
            },

            genBangUrl: function (uri) {
                return methods.genInstanceUrl(uri) + "/bang";
            },

            extractInstanceURIFromHref: function () {
                return decodeURIComponent($(this).attr('href').split('/').pop());
            },

            extractInstanceURIFromHashtag: function () {
                var loc = window.location.href.split('#')[1].split('/'),
                    i = $.inArray("instance", loc);
                return (i !== -1 && loc.length > i) ? decodeURIComponent(loc[i + 1]) : "";
            },

            authenticate: function (data) {
                var d;
                for (d in data) {
                    if (data.hasOwnProperty(d)) {
                        $(this).slapos('store', d, data[d]);
                    }
                }
            },

            isAuthenticated: function () {
                // TODO
                return true;
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
            // DEFAULT ERROR PAGE
            noRoute: function (params) {
                $.router.routes.add('/notfound', 1, methods.showNotFound, $(":jqmData(role=page)"));
                $.router.redirect('/notfound');
            },

            showNotFound: function (params) {
                return this.each(function () {
                    var options = {
                        'title': 'Error',
                        'mainPanel': $(this).vifib('getRender', 'notfoundPanel')
                    };
                    $(this).vifib('render', 'error', options);
                });
            },

            // ROOT
            showRoot: function (params) {
                var route = $.router.routes.current,
                    nextLevel = route.level + 1;
                //$(this).vifib('render', 'root');
                $.router.routes.add('/homepage', nextLevel, methods.showHomepage, $(":jqmData(role=page)"));
                $.router.routes.add('/library', nextLevel, methods.showLibrary, $(":jqmData(role=page)"));
                $.router.routes.add('/documentation', nextLevel, methods.showDocumentation, $(":jqmData(role=page)"));
                $.router.routes.add('/dashboard', nextLevel, methods.showDashboard, $(":jqmData(role=page)"));
                $.router.routes.add('/instance', nextLevel, methods.showInstanceRoot, $(":jqmData(role=page)"));
                $.router.routes.add('/login', nextLevel, methods.showLogin, $(":jqmData(role=page)"));
                // default page
                if ($.router.routes.isCurrent(params.route)) {
                    $.router.redirect('/homepage');
                } else {
                    $.router.start(params.route, nextLevel, methods.noRoute);
                }
            },

            //HOMEPAGE
            showHomepage: function (params) {
                return this.each(function () {
                    var options = {
                            'title': 'Vifib',
                            'mainPanel': $(this).vifib('getRender', 'homepagePanel'),
                            'headmenu': true,
                            'headlinks': [
                                {'name': 'Software library', 'link': '#/library'},
                                {'name': 'Documentation', 'link': '#/documentation'}
                            ]
                        };
                    $(this).vifib('render', 'homepage', options);
                    if ( Modernizr.csstransforms ) {
                        window.mySwipe = new Swipe(document.getElementById('slider'), {
                            speed: 800,
                            auto: 5000
                        });
                    }
                });
            },
            //LOGIN
            showLogin: function (params) {
                return this.each(function () {
                    var mainPanel = $(this).vifib('getRender', 'loginPanel'),
                        options = {
                            'title': 'Vifib',
                            'mainPanel': mainPanel,
                            'leftbutton': {
                                'link': '#/homepage',
                                'icon': 'home',
                                'title': 'Homepage'
                            }
                        },
                        nextLevel = $.router.routes.current.level + 1;
                    $(this).vifib('render', 'login', options);
                });
            },
            // DASHBOARD
            showDashboard: function (params) {
                return this.each(function () {
                    var mainPanel = $(this).vifib('getRender', 'dashboardPanel'),
                        options = {
                            'title': 'Dashboard',
                            'mainPanel': mainPanel
                        };
                    $(this).vifib('render', 'dashboard', options);
                });
            },
            // LIBRARY
            showLibrary: function (params) {
                return this.each(function () {
                    var i, item, nextLevel,
                        /* FAKE ************/
                        data = {
                            'most': [
                                {'link': '#/library/software/kvm', 'name': 'Kvm'},
                                {'link': '#/library/software/kvm', 'name': 'Kvm'},
                            ],
                            'new': [
                                {'link': '#/library', 'name': 'Another Kvm'}
                            ],
                            'newCount': '1'
                        },
                        /*******************/
                        options = {
                            'title': 'Library',
                            'mainPanel': $(this).vifib('getRender', 'libraryPanel', data),
                            'leftbutton': {
                                'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                                'icon': 'home',
                                'title': 'Homepage'
                            },
                            'menu': true,
                            'menulinks': [
                                {'link': '#/library/all', 'name': 'All softwares'}
                            ],
                            'footlinks': [
                                {'link': '#/library', 'name': 'Library'},
                                {'link': '#/documentation', 'name': 'Documentation'}
                            ],
                        };
                    $(this).vifib('render', 'library', options);
                    nextLevel = $.router.routes.current.level + 1;
                    $.router.routes.add('/library/all', nextLevel, methods.showLibraryAll, $(this));
                    $.router.routes.add('/library/categories', nextLevel, methods.showCatalogAll, $(this));
                    /* FAKE *********/
                    $.router.routes.add('/library/software/:software_url', nextLevel, methods.showSoftware, $(this));
                    /****************/
                    $.router.start(params.route, nextLevel, methods.noRoute);
                });
            },

            fillRowSoftware: function (uri) {
                return this.each(function () {
                    $(this).slapos('softwareInfo', uri, {
                        success: function (response) {
                            if (typeof (response) !== "object") {
                                response = $.parseJSON(response);
                            }
                            $.extend(response, {'software_url': methods.genSoftwareUrl(uri)});
                            $(this).vifib('render', 'software.listitem', response);
                        }
                    })
                });
            },

            showLibraryAll: function (params) {
                return this.each(function () {
                    var options = {
                        'title': 'All softwares',
                        'mainPanel': $(this).vifib('getRender', 'library.allPanel'),
                        'leftbutton': {
                            'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                            'icon': 'home',
                            'title': 'Homepage'
                        }
                    },
                        listview = $(this).vifib('render', 'library.all', options).find('#software-list');
                    $(this).slapos('softwareList', {
                        success: function (response) {
                            if (typeof (response) !== "object") {
                                response = $.parseJSON(response);
                            }
                            $.each(response.list, function () {
                                var url = this.toString(),
                                    row = $('<li></li>').vifib('fillRowSoftware', url);
                                listview.append(row).listview('refresh');
                            })
                        }
                    })
                });
            },

            showSoftware: function (params) {
                return this.each(function () {
                    $(this).slapos('softwareInfo', params.software_url, {
                        success: function (response) {
                            var options = {
                                'title': response.name,
                                'mainPanel': $(this).vifib('getRender', 'softwarePanel', response),
                                'leftbutton': {
                                    'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                                    'icon': 'home',
                                    'title': 'Homepage'
                                },
                                'menu': true,
                                'menulinks': [
                                    {'link': '#/library/all', 'name': 'All softwares'}
                                ],
                                'menu-extension': 'From the same category',
                                'menuextlinks': [
                                    {'link': '#/library/software/html5', 'name': 'Html5 AS'}
                                ]
                            }
                            $.extend(options, response)
                            $(this).vifib('render', 'software', options);
                        }
                    })
                });
            },
            // SERVICES // INSTANCES
            showInstanceList: function (params) {
                return this.each(function () {
                    var nextLevel = $.router.routes.current.level + 1,
                        statusCode = {
                            401: redirect,
                            402: payment,
                            404: notFound,
                            500: serverError,
                            503: serverError
                        },
                        options = {
                            'title': 'My Services',
                            'mainPanel': $(this).vifib('getRender', 'instance.list'),
                            'leftbutton': {
                                'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                                'icon': 'home',
                                'title': 'Homepage'
                            },
                            'rightbutton': {
                                'link': '/instance/new',
                                'icon': 'plus',
                                'title': 'add service'
                            }
                        },
                        listview = $(this).vifib('render', 'instance', options).find('#instance-list');
                    // Routing
                    $.router.routes.add('/instance/id/:id', nextLevel, methods.showInstance, $(this));
                    if (params.route !== '/instance') {
                        $.router.start(params.route, nextLevel, methods.noRoute);
                    } else {
                        //table.vifib('refresh', methods.refreshListInstance, 30);
                        $(this).slapos('instanceList', {
                            success: function (data) {
                                if (typeof (data) !== "object") {
                                    data = $.parseJSON(data);
                                }
                                $.each(data.list, function () {
                                    var url = this.toString(),
                                        row = $('<li></li>').vifib('fillRowInstance', url);
                                    //row.vifib('refresh', methods.refreshRowInstance, 30);
                                    listview.append(row).listview('refresh');
                                });
                            },
                            statusCode: statusCode
                        });
                    }
                });
            },

            fillRowInstance: function (url) {
                return this.each(function () {
                    $(this).slapos('instanceInfo', url, {
                        success: function (instance) {
                            if (typeof (instance) !== "object") {
                                instance = $.parseJSON(instance);
                            }
                            $.extend(instance, {'instance_url': methods.genInstanceUrl(url)});
                            $(this).vifib('render', 'instance.listitem', instance);
                        }
                    });
                });
            },
            
            showInstanceRoot: function (params) {
                return this.each(function () {
                    var nextLevel = $.router.routes.current.level + 1,
                        options = {
                            'title': 'Service',
                            'menu': 'true',
                            'leftbutton': {
                                'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                                'icon': 'home',
                                'title': 'Homepage'
                            },
                            'menulinks': [
                                {'link': '#/instance', 'name': 'All services'}
                            ],
                        };
                    $(this).vifib('render', 'instance', options);
                    $.router.routes.add('/instance/list', nextLevel, methods.showInstanceList, $(this).find('.content-primary'));
                    $.router.routes.add('/instance/id/:id', nextLevel, methods.showInstance, $(this).find('.content-primary'));
                    $.router.routes.add('/instance/id/:id/bang', nextLevel, methods.showBangInstance, $(this).find('.content-primary'));
                    if ($.router.routes.isCurrent(params) === false) {
                        $.router.start(params.route, nextLevel, methods.noRoute);
                    }
                });
            },

            showInstance: function (params) {
                return this.each(function () {
                    var statusCode = {
                        401: redirect,
                        402: payment,
                        404: notFound,
                        500: serverError
                    },
                        nextLevel = $.router.routes.current.level + 1;
                    $(this).slapos('instanceInfo', params.id, {
                        success: function (response) {
                            if (typeof (response) !== "object") {
                                response = $.parseJSON(response);
                            }
                            var content = {
                                'information': [
                                    {'name': 'Reference', 'value': response.instance_id},
                                    {'name': 'Status', 'value': response.status},
                                    {'name': 'Software release', 'value': response.software_release},
                                    {'name': 'Software type', 'value': response.software_type}
                                ],
                                'actions': [
                                    {'name': 'Bang', 'link': methods.genBangUrl(params.id)},
                                    {'name': 'Rename', 'link': '#/instance/rename'}
                                ]
                            };
                            //response.status = $(this).vifib('getRender', 'instance.' + response.status);
                            response.actions = [
                                {'name': "Bang", 'url': methods.genBangUrl(decodeURIComponent(params.id))}
                            ];
                            $.extend(response, content);
                            $(this).vifib('render', 'instancePanel', response);
                            //var form = $(this).find("#instance-form");
                            //form.vifib('prepareForm');
                        },
                        statusCode: statusCode
                    });
                })
            },

            showBangInstance: function (params) {
                var statusCode = {
                    400: bad_request,
                    401: redirect,
                    402: payment,
                    404: notFound,
                    500: serverError
                };
                return this.each(function () {
                    console.log("plop")
                    $(this).vifib('render', 'instance.bangPanel');
                    $(this).find('#form-bang').submit(function () {
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
                $(this).vifib('requestAsking', data, function () {
                    $(this).vifib('refreshInstanceForm');
                });
            },

            bindStopStartButtons: function () {
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
                        success: function (response) {
                            if (typeof (response) !== "object") {
                                response = $.parseJSON(response);
                            }
                            var status = $(this).vifib('getRender', 'instance.' + response.status);
                            $("[name=software_type]").val(response.software_type);
                            $("#instanceStatus").html(status);
                            $(this).vifib('bindStopStartButtons');
                        }
                    });
                });
            },

            stopInstance: function () {
                $(this).vifib('changeStatusInstance', 'stopped');
                return false;
            },

            startInstance: function () {
                $(this).vifib('changeStatusInstance', 'started');
                return false;
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


            refreshListInstance: function () {
                var currentList = $(this).vifib('getCurrentList');
                $(this).slapos('instanceList', {
                    success: function (data) {
                        if (typeof (data) !== "object") {
                            data = $.parseJSON(data);
                        }
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

            render: function (template, data, raw) {
                raw = raw || true;
                return this.each(function () {
                    $(this).html(ich[template](data, raw));
                    $(this).trigger('pagecreate');
                });
            },

            getRender: function (template, data, raw) {
                raw = raw || true;
                return $('<div></div>').html(ich[template](data, raw)).attr('data-role', 'page');
            },

            renderAppend: function (template, data, raw) {
                raw = raw || true;
                return this.each(function () {
                    $(this).append(ich[template](data, raw));
                    $(this).trigger('pagecreate');
                });

            },

            renderPrepend: function (template, data, raw) {
                raw = raw || true;
                return this.each(function () {
                    $(this).prepend(ich[template](data, raw));
                    $(this).trigger('pagecreate');
                });
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
    $.fn.serializeObject = function () {
        var obj = {};
        $.each(this.serializeArray(), function (i, o) {
            var n = o.name,
                v = o.value;
            obj[n] = obj[n] === undefined ? v
                    : $.isArray(obj[n]) ? obj[n].concat(v)
                    : [ obj[n], v ];
        });
        return obj;
    };
}(jQuery));

$(document).ready(function () {
    $('body').vifib();
});


