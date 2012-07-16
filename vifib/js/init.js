$(document).bind("mobileinit", function () {
    var spinOptions = {color: "#FFFFFF", lines:30, length:0, width:5, radius:7, rotate:0, trail:60, speed:1.6};

    $.vifib = {} || $.vifib;

    //SlapOs configuration
    $(document).slapos({
        // REST API url
        'host': 'http://10.8.2.34/t139/portal_vifib_rest_api/v1',
        // Facebook application id
        'fbappid': '322443267846597',
        // Google application id
        'ggappid': '380290002359.apps.googleusercontent.com'
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
