/** * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */

var methods = {
    // URL GENERATORS / EXTRACTORS
    genInstanceUrl: function (uri) {
        return $.router.genHash(['instance', 'id', encodeURIComponent(uri)]);
    },
    
    genSoftwareUrl: function (uri) {
        return $.router.genHash(['library', 'software', encodeURIComponent(uri)]);
    },

    genBangUrl: function (uri) {
        return methods.genInstanceUrl(uri) + "/bang";
    },

    extractInstanceURIFromHref: function () {
        return decodeURIComponent($(this).attr('href').split('/').pop());
    },

    extractInstanceURIFromHashtag: function () {
        var loc = window.location.href.split('#')[1].split('/'),
            i = $.inArray("instance", loc);
        return (i !== -1 && loc.length > i) ? decodeURIComponent(loc[i + 1]) : "";
    },

    // AUTHENTICATION
    isAuthenticated: function () {
        // TODO
        return true;
    },

    // RENDER
    changePage: function (page) {
        $('body').append($(page));
        $.mobile.changePage($(page), {changeHash: false, transition: $.mobile.defaultPageTransition});
    },

    render: function (template, data, raw) {
        raw = raw || true;
        return this.each(function () {
            $(this).html(ich[template](data, raw));
            $(this).trigger('pagecreate');
        });
    },

    getRender: function (template, data, raw) {
        raw = raw || true;
        return ich[template](data, raw);
    },

    getPageRender: function (template, data, raw) {
        return $('<div></div>').html(methods.getRender(template, data, raw)).attr('data-role', 'page');
    },

    renderAppend: function (template, data, raw) {
        raw = raw || true;
        return this.each(function () {
            $(this).append(ich[template](data, raw));
            $(this).trigger('pagecreate');
        });
    },

    renderPrepend: function (template, data, raw) {
        raw = raw || true;
        return this.each(function () {
            $(this).prepend(ich[template](data, raw));
            $(this).trigger('pagecreate');
        });
    }
};

$.fn.vifib = function (method) {
    if (methods[method]) {
        return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
    } else {
        $.error( 'Method ' +  method + ' does not exist on jQuery.vifib' );
    }
};
