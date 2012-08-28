(function (window, $) {
    'use strict';
    var callbacks = [];
    /* * * * *
     * function render:
     *  this function is the core of rendering process.
     *  
     *  param:
     *      context = the context in which it will show panels
     *      panels = list of panels (object) to display 
     *      header = topbar of the page
     *      
     * * * * */
    $.vifib.render = function (context, panels, header) {
        var page, i, c;
        // If the context is body element, it means that we want to show a entire new page
        if ($('body')[0] === $(context)[0]) {
            // First this function check the window mode (mobile, tablet, desktop)
            // then define how many panels could be displayed.
            if ($.vifib.device === 'desktop' && panels.length > 1) {
                page = $.vifib.multipanel(panels, 3);
            } else if ($.vifib.device === 'tablet' && panels.length > 1) {
                page = $.vifib.multipanel(panels, 2);
            } else { // Mobile
                page = $.vifib.onepanel(context, panels[0]);
            }
            // create and add header to the page
            if (header !== undefined) {
                if (header.hasOwnProperty('template')) {
                    header.data = header.data === undefined ? undefined : header.data;
                    page.prepend(Mustache.render(header.template, header.data));
                } else if (header.hasOwnProperty('title')) {
                    page.prepend(Mustache.render($.vifib.header.main, header));
                }
            }
            // in case of mobile view or if there is only one panel to show, change page with transition
            if (panels[0].template !== $.vifib.panel.blank || (panels[0].template === $.vifib.panel.blank && $.vifib.device !== 'mobile')) {
                $.vifib.changepage($(page));
            }
        } else { // if the context is a panel just refresh it
            $.vifib.replacepanel($(context), panels[0]);
        }
        // Finally after show page call functions for each panel (callbacks)
        // reverse to call functions from left panel to right panel
        callbacks.reverse();
        while ((c = callbacks.pop()) !== undefined) {
            c.callback.call(c.context);
        }
    };

    // create one panel (no jqm grid)
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

    // create number of panels contain in the list [panels], but with a maximum of [max]
    $.vifib.multipanel = function (panels, max) {
        var page = $('<div data-role="page"></div>')
            .append($.vifib.makecontent(panels, max));
        return $(page);
    };

    // replace a panel with another [panel], without refresh the page
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

    // return a panel wrap in a grid block
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

    // create and return grid of panels
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
            }
        }
        return divcontent;
    };

    // remove all id element in the page and call changepage of jqm
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

    // return the nextpanel (orientation: from left to right)
    $.vifib.nextpanel = function (context) {
        var panelname = [['center'], ['left', 'right'], ['left', 'center', 'right']],
            nbpanel = $(':jqmData(role=content)').data('nbpanel') === undefined ? 1 : $(':jqmData(role=content)').data('nbpanel'),
            panelindex = panelname[nbpanel - 1].indexOf($(context).data('panel-position')),
            nextpanelindex = panelindex === panelname[nbpanel - 1].length - 1 ? panelindex : panelindex + 1;
        return nbpanel > 1 ? $(':jqmData(panel-position=' + panelname[nbpanel - 1][nextpanelindex] + ')') : $(context);
    };
}(window, jQuery));
