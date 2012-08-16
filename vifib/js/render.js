(function (window, $) {
    'use strict';
    var callbacks = [];
    $.vifib.render = function (context, panels, header) {
        var page, i, c;
        if ($('body')[0] === $(context)[0]) {
            if ($.vifib.device === 'desktop' && panels.length > 1) {
                page = $.vifib.multipanel(panels, 3);
            } else if ($.vifib.device === 'tablet' && panels.length > 1) {
                page = $.vifib.multipanel(panels, 2);
            } else { // Mobile
                page = $.vifib.onepanel(context, panels[0]);
            }
            if (header !== undefined) {
                if (header.hasOwnProperty('template')) {
                    header.data = header.data === undefined ? undefined : header.data;
                    page.prepend(Mustache.render(header.template, header.data));
                } else if (header.hasOwnProperty('title')) {
                    page.prepend(Mustache.render($.vifib.header.main, header));
                }
            }
            if (panels[0].template !== $.vifib.panel.blank || (panels[0].template === $.vifib.panel.blank && $.vifib.device !== 'mobile')) {
                $.vifib.changepage($(page));
            }
        } else {
            $.vifib.replacepanel($(context), panels[0]);
            //if ($.vifib.device === 'mobile') {
                //page = $.vifib.onepanel(context, panels[0]);
                //$.vifib.changepage($(page));
            //} else {
                //$.vifib.replacepanel($(context), panels[0]);
            //}
        }
        // reverse to call functions from left panel to right panel
        callbacks.reverse();
        while ((c = callbacks.pop()) !== undefined) {
            c.callback.call(c.context);
        }
    };

    $.vifib.onepanel = function (context, panel) {
        var page = $('<div data-role="page"></div>'),
            content = $('<div data-role="content"></div>'),
            pandata = panel.data === undefined ? {} : panel.data;
        content
            .append(Mustache.render(panel.template, pandata))
            .wrapInner('<section id="panel" data-type="panel"></section>');
        page.append(content);
        if (panel.hasOwnProperty('callback') === true) {
            callbacks.push({callback: panel.callback, context: context});
        }
        return $(page);
    };

    $.vifib.multipanel = function (panels, max) {
        var page = $('<div data-role="page"></div>')
            .append($.vifib.makecontent(panels, max));
        return $(page);
    };

    $.vifib.replacepanel = function (context, panel) {
        var data = panel.hasOwnProperty('data') ? panel.data : {};
        if (context.data('type') !== 'panel') {
            context = context.find(':jqmData(type=panel)');
        }
        context.html(Mustache.render(panel.template, data));
        $(':jqmData(role=page)').trigger('pagecreate');
        if (panel.hasOwnProperty('callback') === true) {
            callbacks.push({callback: panel.callback, context: context});
        }
    };

    $.vifib.makepanel = function (panel, data, index, name) {
        var blockname = [
            'ui-block-a',
            'ui-block-b',
            'ui-block-c',
            'ui-block-d',
            'ui-block-e'
        ],
            divpane = $('<div class="' + blockname[index] + '">')
            .append('<section id="panel-' + name + '" data-type="panel" data-panel-position="' + name + '">' + Mustache.render(panel, data) + '</section>');
        return divpane;
    };

    $.vifib.makecontent = function (panels, max) {
        var i, j,
            pancontext,
            pandata,
            nbpanel = panels.length > max ? max : panels.length,
            panelname = [['center'], ['left', 'right'], ['left', 'right', 'center']],
            gridname = {
                2: 'ui-grid-a',
                3: 'ui-grid-b',
                4: 'ui-grid-c',
                5: 'ui-grid-d'
            },
            divcontent = $('<div data-role="content" data-nbpanel="' + nbpanel + '" class="' + gridname[nbpanel] + '"></div>');
        // reverse loop to place the main panel at right side
        for (i = nbpanel - 1, j = 0; i >= 0; i -= 1, j += 1) {
            pandata = panels[i].data === undefined ? {} : panels[i].data;
            pancontext = $($.vifib.makepanel(panels[i].template, pandata, j, panelname[nbpanel - 1][j]));
            divcontent.append(pancontext);
            if (panels[i].hasOwnProperty('callback')) {
                callbacks.push({callback: panels[i].callback, context: pancontext});
                //panels[i].callback.call(pancontext);
            }
        }
        return divcontent;
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

    $.vifib.nextpanel = function (context) {
        var panelname = [['center'], ['left', 'right'], ['left', 'center', 'right']],
            nbpanel = $(':jqmData(role=content)').data('nbpanel') === undefined ? 1 : $(':jqmData(role=content)').data('nbpanel'),
            panelindex = panelname[nbpanel - 1].indexOf($(context).data('panel-position')),
            nextpanelindex = panelindex === panelname[nbpanel - 1].length - 1 ? panelindex : panelindex + 1;
        return nbpanel > 1 ? $(':jqmData(panel-position=' + panelname[nbpanel - 1][nextpanelindex] + ')') : $(context);
    };
}(window, jQuery));
