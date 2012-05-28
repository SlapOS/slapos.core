(function ($) {
    'use strict';
    $.extend({
        router: {
            routes: {
                list: [],
                add: function (route, level, callback, context) {
                    if (typeof this.list[level] === 'undefined') {
                        this.list[level] = [];
                    }
                    var r = {
                        'route': route,
                        'level': level,
                        'callback': function (params) {
                            if (callback !== undefined) {
                                if (context !== undefined) {
                                    callback(params);
                                } else {
                                    callback.call(context, params);
                                }
                            }
                        }
                    },
                        i = this.list[level].length;
                    this.list[level][i] = r;
                },
                clean: function (level) {
                    this.list = this.list.slice(0, level);
                },
                cleanAll: function () {
                    this.list = this.list.slice(0, 0);
                }
            },
            hashHandler: function () {
                var newHash = window.location.href.split('#')[1];
                console.log('hash change to : ' + newHash);
            },
        }
    });

    $(window).bind('hashchange', $.router.hashchangeHandler);
}(jQuery));
