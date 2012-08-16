$(document).bind('mobileinit', function () {
    'use strict';
    var spinOptions = {color: '#FFFFFF', lines: 30, length: 0, width: 5, radius: 7, rotate: 0, trail: 60, speed: 1.6};

    if (!$.vifib) {
        $.vifib = {};
        $.vifib.pages = {};
    }
    // Initialize routes
    $.vifib.initroutes = function () {
        // Google redirection
        $('body')
            .route('add', $.vifib.pages.login.googleRedirect.url)
            .done($.vifib.pages.login.googleRedirect.action);
        // Authentication
        $('body')
            .route('add', $.vifib.pages.login.dispatch.url)
            .done($.vifib.pages.login.dispatch.action);
        // Default
        $('body')
            .route('add', '')
            .done($.vifib.pages.overview.action);
        // Overview
        $('body')
            .route('add', $.vifib.pages.overview.url)
            .done($.vifib.pages.overview.action);
        // Library
        $('body')
            .route('add', $.vifib.pages.library.dispatch.url)
            .done($.vifib.pages.library.dispatch.action);
        $('body')
            .route('add', $.vifib.pages.library.menu.url)
            .done($.vifib.pages.library.menu.action);
        // Dashboard
        $('body')
            .route('add', $.vifib.pages.dashboard.dispatch.url)
            .done($.vifib.pages.dashboard.dispatch.action);
        $('body')
            .route('add', $.vifib.pages.dashboard.menu.url)
            .done($.vifib.pages.dashboard.menu.action);
        // Software
        $('body')
            .route('add', $.vifib.pages.software.dispatch.url)
            .done($.vifib.pages.software.dispatch.action);
        // Instance
        $('body')
            .route('add', $.vifib.pages.instance.dispatch.url)
            .done($.vifib.pages.instance.dispatch.action);
        // Computer
        $('body')
            .route('add', $.vifib.pages.computer.dispatch.url)
            .done($.vifib.pages.computer.dispatch.action);
    };
    //SlapOs configuration
    $(document).slapos({
        // REST API url
        'host': 'http://10.8.2.34/t139/portal_vifib_rest_api/v1',
        // Facebook application id
        'fbappid': '322443267846597',
        // Google application id
        'ggappid': '380290002359.apps.googleusercontent.com'
    });

    // show loading during ajax request
    $(document).ajaxStart(function () {
        $('#loading').spin(spinOptions);
    }).ajaxStop(function () {
        $('#loading').spin(false);
    });

    //$(document).slapos('store', 'host', '/fake');

    $.mobile.ajaxEnabled = false;
    $.mobile.linkBindingEnabled = false;
    $.mobile.hashListeningEnabled = false;
    $.mobile.pushStateEnabled = false;
    // Disable transition
    //$.mobile.defaultPageTransition = 'none';

    // Remove page from DOM when it's being replaced
    $('div[data-role="page"]').live('pagehide', function (event, ui) {
        $(event.currentTarget).remove();
    });
});
