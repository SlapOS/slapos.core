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
                r = {
                    'route': route,
                    'level': level,
                    'callback': function (params) {
                        if (callback !== undefined) {
                            if (context === undefined) {
                                callback(params);
                            } else {
                                callback.call(context, params);
                            }
                        }
                    },
                },
                    i = this.list[level].length;
                if (this.exist(r) === false) {
                    this.list[level][i] = r;
                }
            },

            exist: function (r) {
                var found = false, i = 0;
                while (i < this.list[r.level].length && found === false) {
                    if (this.list[r.level][i].route === r.route) {
                        found = true;
                    }
                    i += 1;
                }
                return found;
            },

            clean: function (level) {
                this.list = this.list.slice(0, level);
            },

            cleanAll: function () {
                this.list = this.list.slice(0, 0);
            },

            search: function (hash, level, failcallback, context) {
                var stop = false,
                    i, j,
                    regex,
                    result,
                    extracted;
                level = level || 0;
                i = this.list.length - 1;
                hash.route = hash.route === "undefined" ? "/" : hash.route;
                while ((stop  === false) && (i >= level)) {
                    j = 0;
                    while ((stop === false) && (j < this.list[i].length)) {
                        extracted = $.router.extractKeys(this.list[i][j].route);
                        regex = new RegExp(extracted.regex);
                        if (regex.test(hash.route)) {
                            result = regex.exec(hash.route);
                            stop = true;
                            result.shift();
                            for (var k = 0; k < result.length; k += 1) {
                                hash[extracted.keys[k]] = result[k];
                            }
                            this.current = this.list[i][j];
                            this.clean(this.list[i][j].level + 1);
                            this.list[i][j].callback(hash);
                        }
                        j += 1;
                    }
                    i -= 1;
                }
                if (stop === false) {
                    failcallback.call(context);
                }
            },

            isLastLevel: function () {
                return this.current.level === (this.list.length - 1);
            },

            isCurrent: function (hash) {
                var extracted = $.router.extractKeys(this.current.route),
                    regex = new RegExp('^' + extracted.regex + '$');
                return regex.test(hash);
            }
        },

        start: function (hash, level) {
            var hashInfo = this.parseHash(hash);
            if ($.router.routes.current.route !== hashInfo.route) {
                this.routes.search(hashInfo, level);
            }
        },

        redirect: function (hash) {
            var hashInfo = this.parseHash(hash);
            this.routes.search(hashInfo);
        },

        extractKeys: function (regex) {
            var re_key = new RegExp(/:(\w+)/),
                keys = [],
                result;
            while (re_key.test(regex)) {
                result = re_key.exec(regex);
                keys.push(result[1]);
                regex = regex.replace(result[0], '([^\/]+)');
            }
            return {'regex': regex, 'keys': keys}
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

        genHash: function (components) {
            return '#/' + components.join('/');
        },

        parseHash: function (hashTag) {
            var re = new RegExp(/(?:^#?([a-zA-Z0-9\/_-]+))(?:\?([A-Za-z0-9\/&=_-]+))?/g),
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
                hashInfo = $.router.parseHash(hashTag);
            $.router.routes.search(hashInfo)
        },
    }
});

$(window).bind('hashchange', $.router.hashHandler);
$(window).bind('load', $.router.hashHandler);
