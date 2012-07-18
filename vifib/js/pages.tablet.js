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
        page.prepend(Mustache.render($.vifib.header.default, {title: 'Vifib'}));
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
                ],categories: [
                    {url: '#/library/categorie/vm', name: 'Virtual Machine'},
                    {url: '#/library/categorie/db', name: 'Database'}
                ]}
            ]);
            // header
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Library'}));
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
                .fail(function () { $.vifib.replacepanel($(this), $.vifib.panel.failed)});
        },
        overview: function () {
            $.vifib.replacepanel($(this), $.vifib.panel.library, {
                most: [{url: '#/library/software/id/fake/software_info/kvm', name: 'Kvm'},],
                newest: [{url: '#/library/software/id/fake/software_info/html5', name: 'html5 AS'}]
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
                    {url: '#/dashboard/instance/list', name: 'Instances'},
                    {url: '#/dashboard/computer/list', name: 'Computers'}
                ]}
            ]);
            page.prepend(Mustache.render($.vifib.header.default, {title: 'Dashboard'}));
            $.vifib.changepage($(page));
            $('#panel-1')
                .route('add', '/dashboard/', 1)
                .done($.vifib.tablet.dashboard.instancelist);
            $('#panel-1')
                .route('add', '/dashboard/instance/list', 1)
                .done($.vifib.tablet.dashboard.instancelist);
            $('#panel-1')
                .route('add', '/dashboard/instance/id/<instid>', 1)
                .done($.vifib.tablet.dashboard.instance);
            $('#panel-1')
                .route('add', '/dashboard/computer/list', 1)
                .done($.vifib.tablet.dashboard.computerlist);
            $('#panel-1')
                .route('add', '/dashboard/computer/id/<compid>', 1)
                .done($.vifib.tablet.dashboard.computer);
            $('#panel-1')
                .route('go', $.url.getPath(), 1)
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
                },
                statusCode: $.extend(false, $.vifib.statuscode, {
                    404: function (jqxhr, textstatus) {
                        $.vifib.replacepanel($(this), $.vifib.panel.noinstance, {name: instid});
                    }
                })
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
                },
                statusCode: $.extend(false, $.vifib.statuscode, {
                    404: function (jqxhr, textstatus) {
                        $.vifib.replacepanel($(this), $.vifib.panel.nocomputer, {name: compid});
                    }
                })
            });
        }
    }
};
