(function (window, $) {
    'use strict';
    var mainmenudata;
    $.vifib.pages.overview = {
        url: '/overview',
        action: function (args) {
            var ccarousel = function () {
                if (Modernizr.csstransforms) {
                    window.mySwipe = new Swipe(document.getElementById('slider'), {
                        speed: 800,
                        auto: 4000,
                        continous: true
                    });
                }
            },
                clogin = function () {};
            $.vifib.render($('body'), [
                {template: $.vifib.panel.login, callback: clogin},
                {template: $.vifib.panel.menu.main, data: mainmenudata},
                {template: $.vifib.panel.carousel, callback: ccarousel}
            ], {template: $.vifib.header.main, data: {title: 'SlapOs'}});
        }
    };
    mainmenudata = {
        links: [
            {url: $.vifib.buildurl($.vifib.pages.library.overview), name: 'Library'}
        ]
    };
}(window, jQuery));
