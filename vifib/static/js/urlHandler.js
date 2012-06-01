/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/18/12
 */


/**
 * @param {String} hashTag hashTag.
 * @return {String} a clean hashtag.
 */
$.parseHash = function(hashTag) {
    var tokenized = $.extractAuth(hashTag);
    if (tokenized) {
        $.publish('auth', tokenized);
        location.hash = hashTag.split('&')[0];
        return location.hash;
    }
    return hashTag;
};

$.extractAuth = function (hashTag) {
    var del = hashTag.indexOf('&');
    if (del != -1) {
        var splitted = hashTag.substring(del + 1).split('&');
        var result = {};
        for (p in splitted) {
            var s = splitted[p].split('=');
            result[s[0]] = s[1];
        }
        return result;
    }
    return false;
};

$.genHash = function(url) {
    return '#/' + url.join('/');
};

/* Pub / Sub Pattern
    WARNING
    What's happening when we destroy a DOM object subscribed ?
*/
var o = $({});

$.subscribe = function() {
    o.on.apply(o, arguments);
};
$.unsubscribe = function() {
    o.off.apply(o, arguments);
};
$.publish = function() {
    o.trigger.apply(o, arguments);
};

// Event Handlers
$.hashHandler = function(){ $.publish('urlChange', $.parseHash(window.location.href.split("#")[1])); };
$.redirectHandler = function(e, url){ window.location.hash = $.genHash(url); };

// redirections manager
$.redirect = function(url){ $.publish('redirect', [url]); };
$.subscribe('redirect', $.redirectHandler)

console.log("plop")

$(window).bind('hashchange', $.hashHandler);
$(window).bind('load', $.hashHandler);
