(function (window, $) {
    'use strict';
    /* Tools to store js object in sessionStorage */
    var storejs = {
        add: function (key, js) {
            window.sessionStorage.setItem(key, JSON.stringify(js));
        },
        get: function (key) {
            return JSON.parse(window.sessionStorage.getItem(key));
        },
        extend: function (key, object) {
            var data = storejs.get(key);
            $.extend(data, object);
            storejs.add(key, data);
        }
    }

    /*************
     * RESOURCES
     *************/
    // INSTANCE
    storejs.add('instances', {
        Kvm: {
            status: "start_requested",
            connection: {},
            partition: {
                public_ip: [],
                tap_interface: "",
                private_ip: []
            },
            slave: false,
            children_list: [],
            title: "Kvm",
            software_type: "Virtual machine",
            parameter: {
                Custom1: "one string",
                Custom2: "one float",
                Custom3: "[u'abc', u'def']"
            },
            software_release: "http://example.com/example.cfg",
            sla: {
                computer_id: "COMP-0"
            }
        }
    });
    // SOFTWARE
    storejs.add('softwares', {
        Kvm: {
            name: 'Kvm',
            image_url: 'http://www.linux-kvm.org/wiki/skins/kvm/kvmbanner-logo2.png',
            thumb_url: 'http://www.system-linux.eu/public/images/kvm-logo.png',
            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae metus a est convallis pretium. Pellentesque habitant morbi tristique senectus.',
            price: '1'
        },
        Html5as : {
            name: 'Html5as',
            image_url: 'http://7.mshcdn.com/wp-content/uploads/2011/01/html5-logo-1.jpg',
            thumb_url: 'http://www.w3.org/html/logo/downloads/HTML5_Badge_512.png',
            description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae metus a est convallis pretium. Pellentesque habitant morbi tristique senectus.',
            price: '1337'
        }
    });
    // Resources lists
    storejs.add('software_list', {
        list: [
            '/fake/software_info/Kvm',
            '/fake/software_info/Html5as'
        ]
    });

    var fakeserver = sinon.fakeServer.create(),
        tmp = $.ajax,

    /*********************
     *  RESPONSE
     *********************/

    // ******* INSTANCE
        instance_list = function () {
            var response = {list: []};
            $.each(storejs.get('instances'), function (i, e) {
                response.list.push('/fake/instance_info/' + e.title);
            });
            return response;
        };
    // list
    fakeserver.respondWith('GET', '/fake/instance', function (xhr) {
        var response = {list: []};
        $.each(storejs.get('instances'), function (i, e) {
            response.list.push('/fake/instance_info/' + e.title);
        });
        xhr.respond(200, {'Content-Type': 'application/json'}, JSON.stringify(response));
    });
    // Get instance info
    fakeserver.respondWith("GET", /\/fake\/instance_info\/(.*)/, function (xhr, instid) {
        var instances = storejs.get('instances');
        if (instances.hasOwnProperty(instid)) {
            xhr.respond(200, {'Content-Type': 'application/json'}, JSON.stringify(instances[instid]));
        } else {
            xhr.respond(404, { 'Content-Type': 'application/json'}, 'Not found');
        }
    });
    // Request instance
    fakeserver.respondWith("POST", '/fake/instance', function (xhr) {
        var instances = storejs.get('instances'),
            inst = JSON.parse(xhr.requestBody),
            iadd = {},
            ilist = instance_list();
        iadd[inst.title] = inst;
        storejs.extend('instances', iadd);
        xhr.respond(201, {'Content-Type': 'application/json'}, JSON.stringify({
            title: inst.title,
            status: inst.status
        }));
    });

    //********** SOFTWARE
    // Get softwares list
    fakeserver.respondWith('GET', '/fake/software', [
        200, {'Content-Type': 'application/json'}, JSON.stringify(storejs.get('software_list'))
    ]);
    // Get software info
    fakeserver.respondWith("GET", /\/fake\/software_info\/(.*)/, function (xhr, softid) {
        var softwares = storejs.get('softwares');
        if (softwares.hasOwnProperty(softid)) {
            xhr.respond(200, {'Content-Type': 'application/json'}, JSON.stringify(softwares[softid]));
        } else {
            xhr.respond(404, { 'Content-Type': 'application/json'}, 'Not found');
        }
    });

    $.ajax = function (url, options) {
        // it will not work with cache set to false
        if (url.hasOwnProperty('cache')) { url.cache = true; }
        var result = tmp(url, options);
        fakeserver.respond();
        return result;
    };

    $(document).slapos('store', 'host', '/fake');
}(window, jQuery));
