//LOGIN
$.extend(methods, {
    showLogin: function (params) {
        return this.each(function () {
            var mainPanel = $(this).vifib('getRender', 'loginPanel'),
                options = {
                    'title': 'Vifib',
                    'mainPanel': mainPanel,
                    'leftbutton': {
                        'link': '#/homepage',
                        'icon': 'home',
                        'title': 'Homepage'
                    }
                },
                nextLevel = $.router.routes.current.level + 1;
            $(this).vifib('render', 'login', options);
        });
    },
});
