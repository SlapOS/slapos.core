$.vifib.mobile = {
    nopage: function () {
        var page = $.vifib.onepanel($.vifib.panel.failed);
        page.prepend(Mustache.render($.vifib.header.default, {title: 'Oops'}));
        $.vifib.changepage($(page));
    },
    overview: function (route) {
        var page;
        // rendering
        page = $.vifib.onepanel($.vifib.panel.login);
        // header
        page.prepend(Mustache.render($.vifib.header.default, {title: 'Vifib'}));
        // footer navbar
        page.append($.vifib.footer.overview);
        // rendering
        $.vifib.changepage($(page));
    },
    library: {
        dispatch: function (route) {
            $('body')
                .route('add', '/library/', 1)
                .done($.vifib.mobile.library.overview);
            $('body')
                .route('add', '/library/software/id<path:softid>', 1)
                .done($.vifib.mobile.library.software);
            $('body')
                .route('add', '/library/all', 1)
                .done($.vifib.mobile.library.all);
            $('body')
                .route('go', $.url.getPath(), 1)
                .fail($.vifib.mobile.nopage);
        },
        overview: function () {
            page = $.vifib.onepanel($.vifib.panel.library, {
                most: [
                    {url: '#/library/software/id/fake/software_info/kvm', name: 'Kvm'},
                ],
                newest: [
                    {url: '#/library/software/id/fake/software_info/html5', name: 'html5 AS'}
                ]
            });
            // header
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Library'}));
            page.append(Mustache.render($.vifib.panel.simplelist, {
                links: [
                    {url: '#/library/all', name: 'See all softwares'},
                    {url: '#/library/categories', name: 'See categories'}
                ]
            }));
            // footer navbar
            page.append($.vifib.footer.overview);
            // rendering
            $.vifib.changepage($(page));
        },
        software: function (softid) {
            $('body').slapos('softwareInfo', softid, {
                success: function (response) {
                    var page;
                    page = $.vifib.onepanel($.vifib.panel.software, response);
                    // header
                    page.prepend(Mustache.render($.vifib.header.default, {title: response.name}));
                    // footer navbar
                    page.append($.vifib.footer.overview);
                    // rendering
                    $.vifib.changepage($(page));
                }
            });
        },
        all: function () {
            var page = $.vifib.onepanel($.vifib.panel.allsoftware);
            $.vifib.softwareList($(page));
            page.prepend(Mustache.render($.vifib.header.default, {title: 'All softwares'}));
            page.append($.vifib.footer.overview);
            $.vifib.changepage($(page));
        }
    },
    dashboard: {
        dispatch: function (route) {
            $('body')
                .route('add', '/dashboard/', 1)
                .done($.vifib.mobile.dashboard.home);
            $('body')
                .route('add', '/dashboard/instance/list', 1)
                .done($.vifib.mobile.dashboard.instancelist);
            $('body')
                .route('add', '/dashboard/instance/request', 1)
                .done($.vifib.mobile.dashboard.instancerequest);
            $('body')
                .route('add', '/dashboard/instance/id<path:instid>', 1)
                .done($.vifib.mobile.dashboard.instance);
            $('body')
                .route('add', '/dashboard/computer/list', 1)
                .done($.vifib.mobile.dashboard.computerlist);
            $('body')
                .route('add', '/dashboard/computer/id/<compid>', 1)
                .done($.vifib.mobile.dashboard.computer);
            $('body')
                .route('go', $.url.getPath(), 1)
                .fail($.vifib.mobile.nopage);
        },
        home: function (route) {
            var page = $.vifib.onepanel($.vifib.panel.simplelist, {
                links: [
                    {url: '#/dashboard/instance/list', name: 'Instances'},
                    {url: '#/dashboard/computer/list', name: 'Computers'}
                ]
            });
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Dashboard'}));
            $.vifib.changepage($(page));
        },
        instancelist: function (route) {
            var page = $.vifib.onepanel($.vifib.panel.instancelist);
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Instances'}));
            $.vifib.changepage($(page));
            $.vifib.instanceList($(page));
        },
        instancerequest: function (route) {
            var page = $.vifib.onepanel($.vifib.panel.instancerequest);
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Request instance'}));
            $.vifib.changepage($(page));
            $("#instancerequest").submit(function () {
                var data = {
                        "status": "started",
                        "slave": false,
                        "software_release": "http://example.com/example.cfg",
                        "software_type": "type_provided_by_the_software",
                        "parameter": {
                            "Custom1": "one string",
                            "Custom2": "one float",
                            "Custom3": [
                                "abc",
                                "def"
                            ]
                        },
                        "sla": {
                            "computer_id": "COMP-0"
                        }
                    };
                $.extend(data, $(this).serializeObject());
                $(this).slapos('instanceRequest', {
                    data: data,
                    success: function (response) {
                        $.url.redirect('/dashboard/instance/list');
                    }
                });
                return false;
            });
        },
        instance: function (instid) {
            var page;
            $(this).slapos('instanceInfo', instid, {
                success: function (response) {
                    page = $.vifib.onepanel($.vifib.panel.instance, response);
                    page.prepend(Mustache.render($.vifib.header.default, {title: 'Instance'}));
                    $.vifib.changepage($(page));
                }
            });
        },
        computerlist: function (route) {
            var page = $.vifib.onepanel($.vifib.panel.allcomputer);
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Computers'}));
            $.vifib.changepage($(page));
            $.vifib.computerList($(page));
        },
        computer: function (compid) {
            var page;
            $(this).slapos('computerInfo', compid, {
                success: function (response) {
                    page = $.vifib.onepanel($.vifib.panel.computer, response);
                    page.prepend(Mustache.render($.vifib.header.default, {title: 'Computer'}));
                    $.vifib.changepage($(page));
                }
            });
        }
    }
};
