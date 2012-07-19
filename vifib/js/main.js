'use strict';
var getDevice = function (w) {
    return 'mobile';
    if (w < 500) {
        return 'mobile';
    }
    if (w < 900) {
        return 'tablet';
    }
    return 'desktop';
},
    device = getDevice($(window).width());

var body = $("body");

$.vifib.devices = {
    "mobile": function (url) {
        $('body')
            .route('add', '')
            .done($.vifib.mobile.overview);
        $('body')
            .route('add', '/login/facebook')
            .done($.vifib.login.facebook);
        $('body')
            .route('add', '/login/google')
            .done($.vifib.login.google);
        // when oogle send back the token, it reset hashtag from url
        $('body')
            .route('add', 'access_token=<path:path>')
            .done($.vifib.login.googleRedirect);
        $('body')
            .route('add', '/overview')
            .done($.vifib.mobile.overview);
        $('body')
            .route('add', '/library<path:url>')
            .done($.vifib.mobile.library.dispatch);
        $('body')
            .route('add', '/dashboard<path:url>')
            .done($.vifib.mobile.dashboard.dispatch);
    },
    "tablet": function () {
        $('body')
            .route('add', '')
            .done($.vifib.tablet.overview);
        $('body')
            .route('add', '/overview')
            .done($.vifib.tablet.overview);
        $('body')
            .route('add', '/library<path:url>')
            .done($.vifib.tablet.library.dispatch);
        $('body')
            .route('add', '/dashboard<path:url>')
            .done($.vifib.tablet.dashboard.dispatch);
    },
    "desktop": function () {
        $('body')
            .route('add', '')
            .done($.vifib.desktop.redirect);
        $('body')
            .route('add', '<path:url>')
            .done($.vifib.desktop.dispatch);
    }
}

$.vifib.isauthenticated = function () {
    var token_type = $(document).slapos('store', 'token_type');
    if ($(document).slapos('access_token') === undefined || token_type === undefined) {
        return false;
    }
    if (token_type === 'Google') {
    
    } else if (token_type === 'Facebook') {
    
    }
    return false;
}

$.vifib.startrouter = function () {
    $('body')
        .route('go', $.url.getPath())
        .fail($.vifib.mobile.nopage);
}

/* Thanks to Ben Alman
 * https://raw.github.com/cowboy/jquery-misc/master/jquery.ba-serializeobject.js
 */
$.fn.serializeObject = function(){
    var obj = {};
        $.each( this.serializeArray(), function(i,o){
            var n = o.name,
                v = o.value;
            obj[n] = obj[n] === undefined ? v
              : $.isArray( obj[n] ) ? obj[n].concat( v )
              : [ obj[n], v ];
        });
    return obj;
}

$.fn.spin = function(opts) {
    this.each(function() {
        var $this = $(this),
            data = $this.data();
        if (data.spinner) {
            data.spinner.stop();
            delete data.spinner;
        }
        if (opts !== false) {
           data.spinner = new Spinner($.extend({color: $this.css('color')}, opts)).spin(this);
        }
    });
    return this;
}

$(document).ready(function () {
    // bind on resize screen event
    $(window).resize(function () {
        setTimeout(function () {
            var curdevice = getDevice($(window).width());
            if (device !== curdevice) {
                device = curdevice;
                $.routereset();
                $.vifib.devices[device]();
                $.vifib.startrouter();
            }
        }, 800);
    });

    // Url change event
    $.url.onhashchange(function () {
        var options = $.url.getOptions();
        if (options.hasOwnProperty('access_token')) {
            $(document).slapos('access_token', options.access_token);
        }
        $.vifib.devices[device]();
        $.vifib.startrouter();
    });
});
