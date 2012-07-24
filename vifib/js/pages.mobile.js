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
        page.prepend(Mustache.render($.vifib.header.default, {title: 'SlapOs'}));
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
                    {url: '#/library/software/id/fake/software_info/Kvm', name: 'Kvm'},
                ],
                newest: [
                    {url: '#/library/software/id/fake/software_info/Html5', name: 'Html5as'}
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
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
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
                .route('add', '/dashboard/instance/start<path:instid>', 1)
                .done($.vifib.mobile.dashboard.instancestart);
            $('body')
                .route('add', '/dashboard/instance/stop<path:instid>', 1)
                .done($.vifib.mobile.dashboard.instancestop);
            $('body')
                .route('add', '/dashboard/instance/destroy<path:instid>', 1)
                .done($.vifib.mobile.dashboard.instancedestroy);
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
            var page;
            $(this).slapos('instanceInfo', instid, {
                success: function (response) {
                    response[response.status] = true;
                    response.stop_url = '#/dashboard/instance/stop' + instid;
                    response.start_url = '#/dashboard/instance/start' + instid;
                    response.destroy_url = '#/dashboard/instance/destroy' + instid;
                    page = $.vifib.onepanel($.vifib.panel.instance, response);
                    page.prepend(Mustache.render($.vifib.header.default, {title: 'Instance'}));
                    $.vifib.changepage($(page));
                }
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
        instancedestroy: function (instid) {
            $(this).slapos('instanceDelete', instid, {
                success: function (response) {
                    $.url.redirect('/dashboard/instance/id' + instid);
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            })
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
