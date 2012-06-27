/*
 *HOMEPAGE
 */
$.extend(methods, {
    showHomepage: function (params) {
        return this.each(function () {
            var options = {
                    'title': 'Vifib',
                    'mainPanel': $(this).vifib('getRender', 'homepagePanel'),
                    'headmenu': true,
                    'headlinks': [
                        {'name': 'Software library', 'link': '#/library'},
                        {'name': 'Documentation', 'link': '#/documentation'}
                    ]
                };
            $(this).vifib('render', 'homepage', options);
            if ( Modernizr.csstransforms ) {
                window.mySwipe = new Swipe(document.getElementById('slider'), {
                    speed: 800,
                    auto: 5000
                });
            }
        });
    }
});
