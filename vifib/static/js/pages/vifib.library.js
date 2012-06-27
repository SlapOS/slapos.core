/*
 *LIBRARY
 */
$.extend(methods, {
    showLibrary: function (params) {
        return this.each(function () {
            var i, item, nextLevel,
                /* FAKE ************/
                data = {
                    'most': [
                        {'link': '#/library/software/kvm', 'name': 'Kvm'},
                        {'link': '#/library/software/kvm', 'name': 'Kvm'},
                    ],
                    'new': [
                        {'link': '#/library', 'name': 'Another Kvm'}
                    ],
                    'newCount': '1'
                },
                /*******************/
                options = {
                    'title': 'Library',
                    'mainPanel': $(this).vifib('getRender', 'libraryPanel', data),
                    'leftbutton': {
                        'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                        'icon': 'home',
                        'title': 'Homepage'
                    },
                    'menu': true,
                    'menulinks': [
                        {'link': '#/library/all', 'name': 'All softwares'}
                    ],
                    'footlinks': [
                        {'link': '#/library', 'name': 'Library'},
                        {'link': '#/documentation', 'name': 'Documentation'}
                    ],
                };
            $(this).vifib('render', 'library', options);
            nextLevel = $.router.routes.current.level + 1;
            $.router.routes.add('/library/all', nextLevel, methods.showLibraryAll, $(this));
            /* FAKE *********/
            $.router.routes.add('/library/software/:software_url', nextLevel, methods.showSoftware, $(this));
            /****************/
            $.router.start(params.route, nextLevel, methods.noRoute);
        });
    },

    showLibraryAll: function (params) {
        return this.each(function () {
            var options = {
                'title': 'All softwares',
                'mainPanel': $(this).vifib('getRender', 'library.allPanel'),
                'leftbutton': {
                    'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                    'icon': 'home',
                    'title': 'Homepage'
                }
            },
                listview = $(this).vifib('render', 'library.all', options).find('#software-list');
            $(this).slapos('softwareList', {
                success: function (response) {
                    if (typeof (response) !== "object") {
                        response = $.parseJSON(response);
                    }
                    $.each(response.list, function () {
                        var url = this.toString(),
                            row = $('<li></li>').vifib('fillRowSoftware', url);
                        listview.append(row).listview('refresh');
                    })
                }
            })
        });
    },
    fillRowSoftware: function (uri) {
        return this.each(function () {
            $(this).slapos('softwareInfo', uri, {
                success: function (response) {
                    if (typeof (response) !== "object") {
                        response = $.parseJSON(response);
                    }
                    $.extend(response, {'software_url': methods.genSoftwareUrl(uri)});
                    $(this).vifib('render', 'software.listitem', response);
                }
            })
        });
    },

    showSoftware: function (params) {
        return this.each(function () {
            $(this).slapos('softwareInfo', params.software_url, {
                success: function (response) {
                    var options = {
                        'title': response.name,
                        'mainPanel': $(this).vifib('getRender', 'softwarePanel', response),
                        'leftbutton': {
                            'link': $(this).vifib('isAuthenticated') ? '#/dashboard' : '#/homepage',
                            'icon': 'home',
                            'title': 'Homepage'
                        },
                        'menu': true,
                        'menulinks': [
                            {'link': '#/library/all', 'name': 'All softwares'}
                        ],
                        'menu-extension': 'From the same category',
                        'menuextlinks': [
                            {'link': '#/library/software/html5', 'name': 'Html5 AS'}
                        ]
                    }
                    $.extend(options, response)
                    $(this).vifib('render', 'software', options);
                }
            })
        });
    }
});
