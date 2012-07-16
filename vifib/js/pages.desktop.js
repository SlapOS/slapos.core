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
        page.prepend(Mustache.render($.vifib.header.default, {title: 'Vifib'}));
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
            .route('go', $.url.getPath(), 1)
            .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
    },
    overview: function (route) {
        $.vifib.replacepanel($(this), $.vifib.panel.carousel);
        if ( Modernizr.csstransforms ) {
            window.mySwipe = new Swipe(document.getElementById('slider'), {
                speed: 800,
                auto: 4000,
                continous: true
            });
        }
        $.vifib.replacepanel($('#panel-2'), $.vifib.panel.login);
        window.mySwipe.begin();
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
                .route('add', '/library/software/<softid>', 2)
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
                    {url: '#/library/software/kvm', name: 'Kvm'},
                ],
                newest: [
                    {url: '#/library/software/html5', name: 'html5 AS'}
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
                    {url: '#/dashboard/computer/list', name: 'Computers'}
                ]
            });
            $('#panel-2')
                .route('add', '/dashboard/', 2)
                .done($.vifib.desktop.dashboard.instancelist);
            $('#panel-2')
                .route('add', '/dashboard/instance/list', 2)
                .done($.vifib.desktop.dashboard.instancelist);
            $('#panel-2')
                .route('add', '/dashboard/instance/id/<instid>', 2)
                .done($.vifib.desktop.dashboard.instance);
            $('#panel-2')
                .route('add', '/dashboard/computer/list', 2)
                .done($.vifib.desktop.dashboard.computerlist);
            $('#panel-2')
                .route('add', '/dashboard/computer/id/<compid>', 2)
                .done($.vifib.desktop.dashboard.computer);
            $('#panel-2')
                .route('go', $.url.getPath(), 2)
                .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
        },
        instancelist: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.allinstance);
            $.vifib.instanceList($(this));
        },
        instance: function (instid) {
            $(this).slapos('instanceInfo', instid, {
                success: function (response) {
                    $.vifib.replacepanel($(this), $.vifib.panel.instance, response);
                }
            });
        },
        computerlist: function (route) {
            $.vifib.replacepanel($(this), $.vifib.panel.allcomputer);
            $.vifib.computerList($(this));
        },
        computer: function (compid) {
            $(this).slapos('computerInfo', compid, {
                success: function (response) {
                    $.vifib.replacepanel($(this), $.vifib.panel.computer, response);
                }
            });
        }
    }
};
