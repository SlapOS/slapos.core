var comp = {
    computer_id: "COMP-0",
    software: [{software_release: "http://example.com/example.cfg",status: "install"}],
    partition: [
        {title: "slapart1",
            instance_id: "foo",
            status: "start",
            software_release: "http://example.com/example.cfg"},
        {title: "slapart2",
            instance_id: "bar",
            status: "stop",
            software_release: "http://example.com/example.cfg"}
    ]
};

var inst ={
    instance_id: "INST-1",
    status: "stop_requested",
        software_release: "http://example.com/example.cfg",
        software_type: "type_provided_by_the_software",
        slave: "False",
        connection: [{
            key: "foo",
            key: "bar"}],
        parameter: {
            Custom1: "one string",
            Custom2: "one float",
            Custom3: ["abc", "def"]},
        sla: {computer_id: "COMP-0"},
        children_id_list: ["subinstance1", "subinstance2"],
        partition: {
            public_ip: ["::1", "91.121.63.94"],
            private_ip: ["127.0.0.1"],
            tap_interface: "tap2"}
};

var soft = {
    name: 'Kvm',
    image_url: 'http://www.linux-kvm.org/wiki/skins/kvm/kvmbanner-logo2.png',
    thumb_url: 'http://www.system-linux.eu/public/images/kvm-logo.png',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae metus a est convallis pretium. Pellentesque habitant morbi tristique senectus.',
    price: '1',
};

var html5 = {
    name: 'Html5 AS',
    image_url: 'http://smashingweb.ge6.org/wp-content/uploads/2011/01/html5_logo.png',
    thumb_url: 'http://www.w3.org/html/logo/downloads/HTML5_Badge_512.png',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae metus a est convallis pretium. Pellentesque habitant morbi tristique senectus.',
    price: '1337',
};

var software_list = {
    list: [
        'kvm',
        'html5',
        'kvm'
    ]
};

var instance_list = {
    list: [
        'kvm'
    ]
};

var discovery = {
    instance_list: {
        url: '/fake/instance_list',
        method: 'GET'
    },
    instance_info: {
        url: '/fake/instance_info/{instance_url}',
        method: 'GET'
    },
    software_list: {
        url: '/fake/software_list',
        method: 'GET'
    },
    software_info: {
        url: '/fake/software_info/{software_url}',
        method: 'GET'
    }
};

var fakeserver = sinon.fakeServer.create();

// Discovery
fakeserver.respondWith('GET', 'http://10.8.2.34:12006/erp5/portal_vifib_rest_api_v1', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(discovery)
])
// Get instances list
fakeserver.respondWith('GET', '/fake/instance_list', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(instance_list)
]);
// Get instance info
fakeserver.respondWith("GET", '/fake/instance_info/kvm', [
    200, {"Content-Type":"application/json; charset=utf-8"}, JSON.stringify(inst)
]);
// Get softwares list
fakeserver.respondWith('GET', '/fake/software_list', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(software_list)
]);
// Get software info
fakeserver.respondWith('GET', '/fake/software_info/kvm', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(soft)
]);
fakeserver.respondWith('GET', '/fake/software_info/html5', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(html5)
]);

var tmp = $.ajax;
$.ajax = function(url, options){
    // it will not work with cache set to false
    if (url.hasOwnProperty('cache')) { url.cache = true; }
    console.log(url)
    var result = tmp(url, options);
    fakeserver.respond();
    return result;
};
