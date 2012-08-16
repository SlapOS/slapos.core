(function (window, $) {
    'use strict';
    var mainmenudata, librarymenudata;
    $.vifib.pages.library = {
        dispatch: {
            url: '/library<path:url>',
            action: function (args) {
                var p,
                    mainpanel = function () {
                        p = $.routepriority() + 1;
                        $(this)
                            .route('add', $.vifib.pages.library.overview.url, p)
                            .done($.vifib.pages.library.overview.action);
                        $(this)
                            .route('add', $.vifib.pages.library.softwarelist.url, p)
                            .done($.vifib.pages.library.softwarelist.action);
                        $(this)
                            .route('go', $.url.getPath(), p);
                    };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.blank, callback: mainpanel},
                    {template: $.vifib.panel.menu.main, data: librarymenudata},
                    {template: $.vifib.panel.menu.main, data: mainmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        overview: {
            url: '/library/overview',
            action: function (args) {
                $.vifib.render($(this), [
                    {template: $.vifib.panel.library},
                ]);
            }
        },
        menu: {
            url: '/library',
            action: function (args) {
                $.vifib.render($(this), [
                    {template: $.vifib.panel.menu.main, data: librarymenudata},
                    {template: $.vifib.panel.menu.main, data: mainmenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        softwarelist: {
            url: '/library/software/list',
            action: function (args) {
                var softlist = function () {
                    $.vifib.softwareList($(this));
                };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.softwarelist, callback: softlist},
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        }
    };
    $.vifib.pages.software = {
        dispatch: {
            url: '/software<path:url>',
            action: function (args) {
                var p,
                    mainpanel = function () {
                        p = $.routepriority() + 1;
                        $(this)
                            .route('add', $.vifib.pages.software.show.url, p)
                            .done($.vifib.pages.software.show.action);
                        $(this)
                            .route('go', $.url.getPath(), p);
                    },
                    softwarelist = function () {
                        var softlist = function () {
                            $.vifib.softwareList($(this));
                        };
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.softwarelist, callback: softlist},
                        ]);
                    };
                $.vifib.render($(this), [
                    {template: $.vifib.panel.blank, callback: mainpanel},
                    {template: $.vifib.panel.softwarelist, callback: softwarelist},
                    {template: $.vifib.panel.menu.main, data: librarymenudata}
                ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
            }
        },
        show: {
            url: '/software/show<path:softid>',
            action: function (softid) {
                $(this).slapos('softwareInfo', softid, {
                    success: function (response) {
                        $.vifib.render($(this), [
                            {template: $.vifib.panel.software, data: response}
                        ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
                    }
                });
            }
        }

    };
    mainmenudata = {
        links: [
            {url: $.vifib.buildurl($.vifib.pages.library.overview), name: 'Library'}
        ]
    };
    librarymenudata = {
        links: [
            {url: $.vifib.buildurl($.vifib.pages.library.overview), name: 'Overview'},
            {url: $.vifib.buildurl($.vifib.pages.library.softwarelist), name: 'Softwares'}
        ]
    };
}(window, jQuery));
