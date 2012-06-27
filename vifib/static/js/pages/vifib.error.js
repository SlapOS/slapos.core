$.extend(methods, {
    noRoute: function (params) {
        $.router.routes.add('/notfound', 1, methods.showNotFound, $(":jqmData(role=page)"));
        $.router.redirect('/notfound');
    },

    showNotFound: function (params) {
        return this.each(function () {
            var options = {
                'title': 'Error',
                'mainPanel': $(this).vifib('getRender', 'notfoundPanel')
            };
            $(this).vifib('render', 'error', options);
        });
    }
})
