(function (window, $) {
    'use strict';
    $.vifib.onepanel = function (panel, data) {
        var page = $('<div data-role="page"></div>'),
            content = $('<div data-role="content"></div>')
                .append(Mustache.render(panel, data));
        page.append(content);
        return $(page);
    };

    $.vifib.twopanel = function (panels, data) {
        var page = $('<div data-role="page"></div>')
            .append($.vifib.makecontent(panels, data));
        return $(page);
    };

    $.vifib.threepanel = function (panels, data) {
        var page = $('<div data-role="page"></div>')
            .append($.vifib.makecontent(panels, data));
        return $(page);
    };

    $.vifib.replacepanel = function (context, panel, data) {
        context.html(Mustache.render(panel, data));
        $(':jqmData(role=page)').trigger('pagecreate');
    };

    $.vifib.makecontent = function (panels, data) {
        var i = 0,
            pandata,
            gridname = {
                2: 'ui-grid-a',
                3: 'ui-grid-b',
                4: 'ui-grid-c',
                5: 'ui-grid-d'
            },
            divcontent = $('<div data-role="content" class="' + gridname[panels.length] + '"></div>');
        for (i; i < panels.length; i += 1) {
            pandata = data === undefined ? undefined : data[i];
            divcontent.append($.vifib.makepanel(panels[i], pandata, i));
        }
        return divcontent;
    };

    $.vifib.makepanel = function (panel, data, index) {
        var blockname = [
            'ui-block-a',
            'ui-block-b',
            'ui-block-c',
            'ui-block-d',
            'ui-block-e'
        ],
            divpane = $('<div class="' + blockname[index] + '">')
            .append('<section id="panel-' + index + '">' + Mustache.render(panel, data) + '</section>');
        return divpane;
    };

    $.vifib.changepage = function (page) {
        $('[id^=panel]').remove();
        $('#slider').remove();
        $('#loading').remove();
        $('body').append($(page));
        $.mobile.changePage($(page), {
            changeHash: false,
            transition: $.mobile.defaultPageTransition
        });
    };
}(window, jQuery));
