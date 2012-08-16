(function (window, $) {
    'use strict';
    $.vifib.pages.login = {
        dispatch: {
            url: '/login<path:url>',
            action: function (args) {
                $(this)
                    .route('add', $.vifib.pages.login.facebook.url)
                    .done($.vifib.pages.login.facebook.action);
                $(this)
                    .route('add', $.vifib.pages.login.google.url)
                    .done($.vifib.pages.login.google.action);
                $(this)
                    .route('go', $.url.getPath());
            }
        },
        facebook: {
            url: '/login/facebook',
            action: function (args) {
                var redirect = window.location.protocol + '//' + window.location.host + window.location.pathname + $.vifib.buildurl($.vifib.pages.dashboard.menu) + '?',
                    fburl = 'https://www.facebook.com/dialog/oauth?' +
                        'client_id=' + $(document).slapos('store', 'fbappid') +
                        '&redirect_uri=' + encodeURIComponent(redirect) +
                        '&scope=email' +
                        '&response_type=token';
                // set token type to Facebook for js library
                $(document).slapos('store', 'token_type', 'Facebook');
                window.location.href = fburl;
            },
        },
        google: {
            url: '/login/google',
            action: function (args) {
                var redirect = window.location.protocol + '//' + window.location.host + window.location.pathname,
                    ggurl = 'https://accounts.google.com/o/oauth2/auth?' +
                        'client_id=' + $(document).slapos('store', 'ggappid') +
                        '&redirect_uri=' + encodeURIComponent(redirect) +
                        '&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email++https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile' +
                        '&response_type=token';
                $(document).slapos('store', 'token_type', 'Google');
                window.location.href = ggurl;
            }
        },
        googleRedirect: {
            url: 'access_token=<path:path>',
            action: function (response) {
                var options = {},
                    option;
                response = 'access_token=' + response;
                $.each(response.split('&'), function (i, e) {
                    option = e.split('=');
                    options[option[0]] = option[1];
                });
                $.url.redirect('/dashboard', options);
            }
        }
    };
}(window, jQuery));
