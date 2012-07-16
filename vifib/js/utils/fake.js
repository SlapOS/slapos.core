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
    image_url: 'http://7.mshcdn.com/wp-content/uploads/2011/01/html5-logo-1.jpg',
    thumb_url: 'http://www.w3.org/html/logo/downloads/HTML5_Badge_512.png',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae metus a est convallis pretium. Pellentesque habitant morbi tristique senectus.',
    price: '1337',
};

var software_list = {
    list: [
        '/fake/software_info/kvm',
        '/fake/software_info/html5',
    ]
};

var instance_list = {
    list: [
        '/fake/instance_info/kvm'
    ]
};

var computer_list = {
    list: [
        '/fake/computer_info/comp'
    ]
};

var fakeserver = sinon.fakeServer.create();

// Get instances list
fakeserver.respondWith('GET', '/fake/instance', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(instance_list)
]);
// Get instance info
fakeserver.respondWith("GET", '/fake/instance_info/kvm', [
    200, {"Content-Type":"application/json; charset=utf-8"}, JSON.stringify(inst)
]);
// Get softwares list
fakeserver.respondWith('GET', '/fake/software', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(software_list)
]);
// Get software info
fakeserver.respondWith('GET', '/fake/software_info/kvm', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(soft)
]);
fakeserver.respondWith('GET', '/fake/software_info/html5', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(html5)
]);
fakeserver.respondWith('GET', '/fake/software_info/nas', [
    404, {'Content-Type': 'application/json'}, ''
]);
// Get computers list
fakeserver.respondWith('GET', '/fake/computer', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(computer_list)
]);
// Get computer info
fakeserver.respondWith('GET', '/fake/computer_info/comp', [
    200, {'Content-Type': 'application/json'}, JSON.stringify(comp)
]);

var tmp = $.ajax;
$.ajax = function(url, options){
    // it will not work with cache set to false
    if (url.hasOwnProperty('cache')) { url.cache = true; }
    var result = tmp(url, options);
    fakeserver.respond();
    return result;
};
