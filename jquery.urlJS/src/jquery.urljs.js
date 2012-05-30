(function ($) {
    'use strict';
    $.extend({
        router: {
            routes: {
                list: [],
                current: null,
                add: function (route, level, callback, context) {
                    var r, keys, i;
                    if (typeof this.list[level] === 'undefined') {
                        this.list[level] = [];
                    }
                    route = route.replace(/:\w+/g, '([^\/]+)');
                    r = {
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
                        },
                    },
                        i = this.list[level].length;
                    this.list[level][i] = r;
                },
                clean: function (level) {
                    this.list = this.list.slice(0, level);
                },
                cleanAll: function () {
                    this.list = this.list.slice(0, 0);
                },
                search: function (hash) {
                    var stop = false,
                        i = 0,
                        j = 0,
                        regex,
                        result;
                    console.log(hash)
                    while ((stop  === false) && (i < this.list.length)) {
                        while ((stop === false) && (j < this.list[i].length)) {
                            regex = new RegExp('^' + this.list[i][j].route + '$');
                            if (regex.test(hash.route)) {
                                result = regex.exec(hash.route);
                                stop = true;
                                console.log(result)
                                result.shift();
                                //delete hash.route;
                                this.list[i][j].callback(hash);
                            }
                            j += 1;
                        }
                        i += 1;
                    }
                }
            },

            deserialize: function (params) {
                var result = {},
                    p,
                    params = params.split('&');
                while (params.length) {
                    p = params.shift().split('=');
                    if (p[0] !== '') {
                        if (p.length === 2) {
                            result[p[0]] = p[1] === 'true' ? true : p[1];
                        } else {
                            result[p[0]] = true;
                        }
                    }
                }
                return result;
            },

            serialize: function (obj) {
                return $.param(obj);
            },

            parseHash: function (hashTag) {
                var re = new RegExp(/(?:^#([a-zA-Z0-9\/_-]+))(?:\?([A-Za-z0-9\/&=_-]+))?/g),
                    groups = re.exec(hashTag),
                    r, params = {};
                groups.shift();
                // route
                r = groups[0];
                // params
                if (groups[1] !== undefined) {
                    params = this.deserialize(groups[1]);
                }
                return params.length === 0 ? {'route': r} : $.extend({'route': r}, params);
            },

            hashHandler: function () {
                var hashTag = window.location.href.split('#')[1],
                    hashInfo = this.parseHash(hashTag);
                this.routes.call(hashInfo)
            },
        }
    });

    $(window).bind('hashchange', $.router.hashchangeHandler);
    $(window).bind('load', $.router.hashchangeHandler);
}(jQuery));
