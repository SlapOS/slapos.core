(function (window, $) {
    'use strict';
    $.vifib.statuscode = {
        400: function (jqxhr, textstatus) {
            var page;
            if ($.vifib.device === 'mobile') {
                page = $.vifib.onepanel($.vifib.panel.badrequest);
                page.prepend(Mustache.render($.vifib.header.main, {title: 'An error as occured'}));
                page.append($.vifib.footer.overview);
                $.vifib.changepage($(page));
            } else {
                $.vifib.replacepanel($(this), $.vifib.panel.badrequest);
            }
        },
        401: function (jqxhr, textstatus) {
            $.url.redirect('/overview');
        },
        402: function (jqxhr, textstatus) {
            var page;
            if ($.vifib.device === 'mobile') {
                page = $.vifib.onepanel($.vifib.panel.payment);
                page.prepend(Mustache.render($.vifib.header.main, {title: 'An error as occured'}));
                page.append($.vifib.footer.overview);
                $.vifib.changepage($(page));
            } else {
                $.vifib.replacepanel($(this), $.vifib.panel.payment);
            }
        },
        404: function (jqxhr, textstatus) {
            var page;
            if ($.vifib.device === 'mobile') {
                page = $.vifib.onepanel($.vifib.panel.notfound);
                page.prepend(Mustache.render($.vifib.header.main, {title: 'An error as occured'}));
                page.append($.vifib.footer.overview);
                $.vifib.changepage($(page));
            } else {
                $.vifib.replacepanel($(this), $.vifib.panel.notfound);
            }
        },
        500: function (jqxhr, textstatus) {
            var page;
            if ($.vifib.device === 'mobile') {
                page = $.vifib.onepanel($.vifib.panel.internalerror);
                page.prepend(Mustache.render($.vifib.header.main, {title: 'An error as occured'}));
                page.append($.vifib.footer.overview);
                $.vifib.changepage($(page));
            } else {
                $.vifib.replacepanel($(this), $.vifib.panel.internalerror);
            }
        }
    };
    $.vifib.softwareList = function (context) {
        var list;
        return context.each(function () {
            list = $(this).find('ul');
            $(this).slapos('softwareList', {
                success: function (response) {
                    $.each(response.list, function (index, soft) {
                        var row = $.vifib.fillRowSoftware($('<li></li>'), soft);
                        list.append(row);
                    });
                    list.listview('refresh');
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        });
    };
    $.vifib.instanceList = function (context) {
        var list;
        return context.each(function () {
            list = $(this).find('ul');
            $(this).slapos('instanceList', {
                success: function (response) {
                    $.each(response.list, function (i, e) {
                        $.vifib.fillRowInstance(list, $('<li></li>'), e);
                    });
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        });
    };
    $.vifib.fillRowInstance = function (list, row, instid) {
        return row.slapos('instanceInfo', instid, {
            success: function (response) {
                $.extend(response, {insturl: '#/instance/show' + instid});
                $(this).html(Mustache.render($.vifib.panel.rowinstance, response));
            },
            complete: function (jqxhr, textstatus) {
                list.append($(this)).listview('refresh');
            },
            statusCode: $.extend(false, $.vifib.statuscode, {})
        });
    };
    $.vifib.computerList = function (context) {
        var list;
        return context.each(function () {
            list = $(this).find('ul');
            $(this).slapos('computerList', {
                success: function (response) {
                    $.each(response.list, function (index, comp) {
                        var row = $.vifib.fillRowComputer($('<li></li>'), comp);
                        list.append(row);
                    });
                    list.listview('refresh');
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        });
    };
    $.vifib.fillRowSoftware = function (context, softid) {
        return context.each(function () {
            $(this).slapos('softwareInfo', softid, {
                success: function (response) {
                    $.extend(response, {softurl: '#/software/show' + softid});
                    $(this).html(Mustache.render($.vifib.panel.rowsoftware, response));
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        });
    };
    $.vifib.fillRowComputer = function (context, compid) {
        return context.each(function () {
            $(this).slapos('computerInfo', compid, {
                success: function (response) {
                    $.extend(response, {compurl: '#/computer/show' + compid});
                    $(this).html(Mustache.render($.vifib.panel.rowcomputer, response));
                },
                statusCode: $.extend(false, $.vifib.statuscode, {})
            });
        });
    };
    $.vifib.buildurl = function (panel) {
        return '#' + panel.url;
    };
}(window, jQuery));
