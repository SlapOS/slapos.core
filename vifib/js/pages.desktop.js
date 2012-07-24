$.vifib.desktop = {
    redirect: function (route) {
        $.url.go('/overview');
    },
    dispatch: function (route) {
        var page = $.vifib.threepanel([
            $.vifib.panel.sidemenu.main,
            $.vifib.panel.blank,
            $.vifib.panel.blank
        ], [
            {links: [
                {url: '#/library/', name: 'Library'},
                {url: 'http://packages.python.org/slapos.core/', name: 'Documentation'}
            ]}
        ]);
        // header
        page.prepend(Mustache.render($.vifib.header.default, {title: 'SlapOs'}));
        // rendering
        $.vifib.changepage($(page));
        $('#panel-1')
            .route('add', '/library<path:url>', 1)
            .done($.vifib.desktop.library.dispatch);
        $('#panel-1')
            .route('add', '/overview', 1)
            .done($.vifib.desktop.overview);
        $('#panel-1')
            .route('add', '/dashboard<path:url>', 1)
            .done($.vifib.desktop.dashboard.dispatch);
        $('#panel-1')
            .route('add', '/login/facebook', 1)
            .done($.vifib.login.facebook);
        $('#panel-1')
            .route('add', '/login/google', 1)
            .done($.vifib.login.google);
        // when Google send back the token, it reset hashtag from url
        $('#panel-1')
            .route('add', 'access_token=<path:path>', 1)
            .done($.vifib.login.googleRedirect);
        $('#panel-1')
            .route('go', $.url.getPath(), 1)
            .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
    },
    overview: function (route) {
        $.vifib.replacepanel($(this), $.vifib.panel.carousel);
        if (Modernizr.csstransforms) {
            window.mySwipe = new Swipe(document.getElementById('slider'), {
                speed: 800,
                auto: 4000,
                continous: true
            });
        }
        $.vifib.replacepanel($('#panel-2'), $.vifib.panel.login);
    },
    library: {
        dispatch: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.sidemenu.library, {
                links: [
                    {url: '#/library/', name: 'Overview'},
                    {url: '#/library/all', name: 'See all softwares'}
                ],
                categories: [
                    {url: '#/library/categorie/vm', name: 'Virtual Machine'},
                    {url: '#/library/categorie/db', name: 'Database'}
                ]
            });
            $('#panel-2')
                .route('add', '/library/', 2)
                .done($.vifib.desktop.library.overview);
            $('#panel-2')
                .route('add', '/library/software/id<path:softid>', 2)
                .done($.vifib.desktop.library.software);
            $('#panel-2')
                .route('add', '/library/all', 2)
                .done($.vifib.desktop.library.all);
            $('#panel-2')
                .route('go', $.url.getPath(), 2)
                .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
        },
        overview: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.library, {
                most: [
                    {url: '#/library/software/id/fake/software_info/Kvm', name: 'Kvm'},
                ],
                newest: [
                    {url: '#/library/software/id/fake/software_info/Html5as', name: 'html5 AS'}
                ]
            });
        },
        software: function (softid) {
            $(this).slapos('softwareInfo', softid, {
                success: function (response) {
                    $.vifib.replacepanel($(this), $.vifib.panel.software, response);
                }
            });
        },
        all: function () {
            $.vifib.replacepanel($(this), $.vifib.panel.allsoftware);
            $.vifib.softwareList($(this));
        }
    },
    dashboard: {
        dispatch: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.simplelist, {
                links: [
                    {url: '#/dashboard/instance/list', name: 'Instances'},
                ]
            });
            $('#panel-2')
                .route('add', '/dashboard/', 2)
                .done($.vifib.desktop.dashboard.instancelist);
            $('#panel-2')
                .route('add', '/dashboard/instance/list', 2)
                .done($.vifib.desktop.dashboard.instancelist);
            $('#panel-2')
                .route('add', '/dashboard/instance/request', 2)
                .done($.vifib.desktop.dashboard.instancerequest);
            $('#panel-2')
                .route('add', '/dashboard/instance/id<path:instid>', 2)
                .done($.vifib.desktop.dashboard.instance);
            $('#panel-2')
                .route('add', '/dashboard/instance/start<path:instid>', 2)
                .done($.vifib.desktop.dashboard.instancestart);
            $('#panel-2')
                .route('add', '/dashboard/instance/stop<path:instid>', 2)
                .done($.vifib.desktop.dashboard.instancestop);
            $('#panel-2')
                .route('add', '/dashboard/instance/destroy<path:instid>', 2)
                .done($.vifib.desktop.dashboard.instancedestroy);
            $('#panel-2')
                .route('go', $.url.getPath(), 2)
                .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
        },
        instancelist: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.instancelist);
            $.vifib.instanceList($(this));
        },
        instancerequest: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.instancerequest);
            $("#instancerequest").submit(function () {
                var data = {
                        "status": "start_requested",
                        "slave": false,
                        "software_type": "type_provided_by_the_software",
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
        instance: function (instid) {
            $(this).slapos('instanceInfo', instid, {
                success: function (response) {
                    response[response.status] = true;
                    response.stop_url = '#/dashboard/instance/stop' + instid;
                    response.start_url = '#/dashboard/instance/start' + instid;
                    response.destroy_url = '#/dashboard/instance/destroy' + instid;
                    $.vifib.replacepanel($(this), $.vifib.panel.instance, response);
                }
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
                        })
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
                        })
                    }
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        },
    }
};
