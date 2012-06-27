$.extend(methods, {
    showDashboard: function (params) {
        return this.each(function () {
            var mainPanel = $(this).vifib('getRender', 'dashboardPanel'),
                options = {
                    'title': 'Dashboard',
                    'mainPanel': mainPanel
                },
                page = $(this).vifib('getPageRender', 'dashboard', options);
            methods.changePage(page);
        });
    }
});
