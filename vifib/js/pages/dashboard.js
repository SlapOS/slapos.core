(function (window, $) {
    'use strict';
    var mainmenudata, dashboardmenudata;
    $.vifib.pages.dashboard = {
        dispatch: {
            url: '/dashboard<path:url>',
            action: function (args) {
                var p,
                    mainpanel = function () {
                        p = $.routepriority() + 1;
                        $(this)
                            .route('add', $.vifib.pages.dashboard.instancelist.url, p)
                            .done($.vifib.pages.dashboard.instancelist.action);
                        $(this)
                            .route('add', $.vifib.pages.dashboard.instancerequest.url, p)
                            .done($.vifib.pages.dashboard.instancerequest.action);
                        $(this)
                            .route('add', $.vifib.pages.dashboard.computerlist.url, p)
                            .done($.vifib.pages.dashboard.computerlist.action);
                        $(this)
                            .route('go', $.url.getPath(), p);
                    };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.blank, callback: mainpanel},
                    {template: $.vifib.panel.menu.main, data: dashboardmenudata},
                    {template: $.vifib.panel.menu.main, data: mainmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        menu: {
            url: '/dashboard',
            action: function (args) {
                $.vifib.render($(this), [
                    {template: $.vifib.panel.menu.main, data: dashboardmenudata},
                    {template: $.vifib.panel.menu.main, data: mainmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        instancelist: {
            url: '/dashboard/instance/list',
            action: function (args) {
                var instlist = function () {
                    $.vifib.instanceList($(this));
                };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.instancelist, callback: instlist, data: {requesturl: '#/dashboard/instance/request'}},
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        instancerequest: {
            url: '/dashboard/instance/request',
            action: function (args) {
                var instreq = function () {
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
                                $.url.redirect($.vifib.pages.dashboard.instancelist.url);
                            },
                            statusCode: $.extend(false, $.vifib.statuscode, {})
                        });
                        return false;
                    });
                };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.instancerequest, callback: instreq},
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        computerlist: {
            url: '/dashboard/computer/list',
            action: function (args) {
                var complist = function () {
                    $.vifib.computerList($(this));
                };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.computerlist, callback: complist},
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        }
    };
    $.vifib.pages.instance = {
        dispatch: {
            url: '/instance<path:url>',
            action: function (args) {
                var p,
                    mainpanel = function () {
                        p = $.routepriority() + 1;
                        $(this)
                            .route('add', $.vifib.pages.instance.show.url, p)
                            .done($.vifib.pages.instance.show.action);
                        $(this)
                            .route('go', $.url.getPath(), p);
                    },
                    instancelist = function () {
                        var instlist = function () {
                            $.vifib.instanceList($(this));
                        };
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.instancelist, callback: instlist, data: {requesturl: '#/dashboard/instance/request'}},
                        ]);
                    };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.blank, callback: mainpanel},
                    {template: $.vifib.panel.instancelist, callback: instancelist},
                    {template: $.vifib.panel.menu.main, data: dashboardmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        show: {
            url: '/instance/show<path:instid>',
            action: function (instid) {
                $(this).slapos('instanceInfo', instid, {
                    success: function (response) {
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.instance, data: response}
                        ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
                    }
                });
            }
        }
    };
    $.vifib.pages.computer = {
        dispatch: {
            url: '/computer<path:url>',
            action: function (args) {
                var p,
                    mainpanel = function () {
                        p = $.routepriority() + 1;
                        $(this)
                            .route('add', $.vifib.pages.computer.show.url, p)
                            .done($.vifib.pages.computer.show.action);
                        $(this)
                            .route('go', $.url.getPath(), p);
                    },
                    computerlist = function () {
                        var complist = function () {
                            $.vifib.computerList($(this));
                        };
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.computerlist, callback: complist},
                        ]);
                    };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.blank, callback: mainpanel},
                    {template: $.vifib.panel.computerlist, callback: computerlist},
                    {template: $.vifib.panel.menu.main, data: dashboardmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        show: {
            url: '/computer/show<path:compid>',
            action: function (compid) {
                $(this).slapos('computerInfo', compid, {
                    success: function (response) {
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.computer, data: response}
                        ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
                    }
                });
            }
        }
    };
    mainmenudata = {
        links: [
            {url: $.vifib.buildurl($.vifib.pages.library.overview), name: 'Library'},
            {url: $.vifib.buildurl($.vifib.pages.library.overview), name: 'Dashboard'}
        ]
    };
    dashboardmenudata = {
        links: [
            {url: $.vifib.buildurl($.vifib.pages.dashboard.instancelist), name: 'Instances'},
            {url: $.vifib.buildurl($.vifib.pages.dashboard.computerlist), name: 'Computers'}
        ]
    };
}(window, jQuery));
