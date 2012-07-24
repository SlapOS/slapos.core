(function (window, $) {
    'use strict';
    $.vifib.tablet = {
        overview: function (route) {
            var page = $.vifib.twopanel([
                $.vifib.panel.sidemenu.main,
                $.vifib.panel.login
            ], [
                {links: [
                    {url: '#/library/', name: 'Library'},
                    {url: 'http://packages.python.org/slapos.core/', name: 'Documentation'}
                ]}
            ]);
            // header
            page.prepend(Mustache.render($.vifib.header.main, {title: 'SlapOs'}));
            // rendering
            $.vifib.changepage($(page));
        },
        library: {
            dispatch: function (route) {
                var page = $.vifib.twopanel([
                    $.vifib.panel.sidemenu.library,
                    $.vifib.panel.blank
                ], [
                    {links: [
                        {url: '#/library/', name: 'Overview'},
                        {url: '#/library/all', name: 'See all softwares'}
                    ], categories: [
                        {url: '#/library/categorie/vm', name: 'Virtual Machine'},
                        {url: '#/library/categorie/db', name: 'Database'}
                    ]}
                ]);
                // header
                page.prepend(Mustache.render($.vifib.header.main, {title: 'Library'}));
                // rendering
                $.vifib.changepage($(page));
                $('#panel-1')
                    .route('add', '/library/', 1)
                    .done($.vifib.tablet.library.overview);
                $('#panel-1')
                    .route('add', '/library/software/id<path:softid>', 1)
                    .done($.vifib.tablet.library.software);
                $('#panel-1')
                    .route('add', '/library/all', 1)
                    .done($.vifib.tablet.library.all);
                $('#panel-1')
                    .route('go', $.url.getPath(), 1)
                    .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed); });
            },
            overview: function () {
                $.vifib.replacepanel($(this), $.vifib.panel.library, {
                    most: [{url: '#/library/software/id/fake/software_info/Kvm', name: 'Kvm'}],
                    newest: [{url: '#/library/software/id/fake/software_info/Html5as', name: 'html5 AS'}]
                });
            },
            software: function (softid) {
                $(this).slapos('softwareInfo', softid, {
                    success: function (response) {
                        $.vifib.replacepanel($(this), $.vifib.panel.software, response);
                    },
                    statusCode: $.extend(false, $.vifib.statuscode, {
                        404: function (jqxhr, textstatus) {
                            $.vifib.replacepanel($(this), $.vifib.panel.nosoftware, {name: softid});
                        }
                    })
                });
            },
            all: function (softid) {
                $.vifib.replacepanel($(this), $.vifib.panel.allsoftware);
                $.vifib.softwareList($(this));
            }
        },
        dashboard: {
            dispatch: function (route) {
                var page = $.vifib.twopanel([
                    $.vifib.panel.simplelist,
                    $.vifib.panel.blank
                ], [
                    {links: [
                        {url: '#/library/', name: 'Library'},
                        {url: 'http://packages.python.org/slapos.core/', name: 'Documentation'},
                        {url: '#/dashboard/instance/list', name: 'Instances'}
                    ]}
                ]);
                page.prepend(Mustache.render($.vifib.header.main, {title: 'Dashboard'}));
                $.vifib.changepage($(page));
                $('#panel-1')
                    .route('add', '/dashboard/', 1)
                    .done($.vifib.tablet.dashboard.instancelist);
                $('#panel-1')
                    .route('add', '/dashboard/instance/list', 1)
                    .done($.vifib.tablet.dashboard.instancelist);
                $('#panel-1')
                    .route('add', '/dashboard/instance/request', 1)
                    .done($.vifib.tablet.dashboard.instancerequest);
                $('#panel-1')
                    .route('add', '/dashboard/instance/id<path:instid>', 1)
                    .done($.vifib.tablet.dashboard.instance);
                $('#panel-1')
                    .route('add', '/dashboard/instance/start<path:instid>', 1)
                    .done($.vifib.tablet.dashboard.instancestart);
                $('#panel-1')
                    .route('add', '/dashboard/instance/stop<path:instid>', 1)
                    .done($.vifib.tablet.dashboard.instancestop);
                $('#panel-1')
                    .route('add', '/dashboard/instance/destroy<path:instid>', 1)
                    .done($.vifib.tablet.dashboard.instancedestroy);
                $('#panel-1')
                    .route('go', $.url.getPath(), 1)
                    .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed); });
            },
            instancelist: function (route) {
                $.vifib.replacepanel($(this), $.vifib.panel.instancelist);
                $.vifib.instanceList($(this));
            },
            instance: function (instid) {
                $(this).slapos('instanceInfo', instid, {
                    success: function (response) {
                        response[response.status] = true;
                        response.stop_url = '#/dashboard/instance/stop' + instid;
                        response.start_url = '#/dashboard/instance/start' + instid;
                        response.destroy_url = '#/dashboard/instance/destroy' + instid;
                        $.vifib.replacepanel($(this), $.vifib.panel.instance, response);
                    },
                    statusCode: $.extend(false, $.vifib.statuscode, {
                        404: function (jqxhr, textstatus) {
                            $.vifib.replacepanel($(this), $.vifib.panel.noinstance, {name: instid});
                        }
                    })
                });
            },
            instancerequest: function (route) {
                $.vifib.replacepanel($(this), $.vifib.panel.instancerequest);
                $("#instancerequest").submit(function () {
                    var data = {
                            "status": "start_requested",
                            "slave": false,
                            "software_type": "type_provided_by_the_software"
                        };
                    $.extend(data, $(this).serializeObject());
                    $(this).slapos('instanceRequest', {
                        data: data,
                        success: function (response) {
                            $.url.redirect('/dashboard/instance/list');
                        },
                        statusCode: $.extend(false, $.vifib.statuscode, {})
                    });
                    return false;
                });
            },
            instancestop: function (instid) {
                $(this).slapos('instanceInfo', instid, {
                    success: function (response) {
                        if (response.status === 'start_requested') {
                            response.status = 'stop_requested';
                            $(this).slapos('instanceRequest', {
                                data: response,
                                success: function (response) {
                                    $.url.redirect('/dashboard/instance/id' + instid);
                                },
                                statusCode: $.extend(false, $.vifib.statuscode, {})
                            });
                        }
                    },
                    statusCode: $.extend(false, $.vifib.statuscode, {})
                });
            },
            instancestart: function (instid) {
                $(this).slapos('instanceInfo', instid, {
                    success: function (response) {
                        if (response.status === 'stop_requested') {
                            response.status = 'start_requested';
                            $(this).slapos('instanceRequest', {
                                data: response,
                                success: function (response) {
                                    $.url.redirect('/dashboard/instance/id' + instid);
                                },
                                statusCode: $.extend(false, $.vifib.statuscode, {})
                            });
                        }
                    },
                    statusCode: $.extend(false, $.vifib.statuscode, {})
                });
            }
        }
    };
}(window, jQuery));
