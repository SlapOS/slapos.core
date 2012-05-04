var comp0 = {computer_id: "COMP-0",
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

var comp1 = {computer_id: "COMP-1",
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

var inst0 =
    {instance_id: "INST-0",
        status: "start",
        software_release: "http://example.com/example.cfg",
        software_type: "type_provided_by_the_software",
        slave: "False",
        connection: [{
            custom_connection_parameter_1: "foo",
            custom_connection_parameter_2: "bar"}],
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

var inst1 =
    {instance_id: "INST-1",
        status: "start",
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

/*var fakeserver = sinon.fakeServer.create();

// Get instance
fakeserver.respondWith("GET", "/instance/200",[200, {"Content-Type":"application/json; charset=utf-8"}, JSON.stringify(inst0)]);
fakeserver.respondWith("GET", "/instance/201",[200, {"Content-Type":"application/json; charset=utf-8"}, JSON.stringify(inst1)]);
// Get instance FAIL
fakeserver.respondWith("GET", "/instance/408",[408, {"Content-Type":"application/json; charset=utf-8"}, "NOT FOUND"]);
fakeserver.respondWith("GET", "/instance/401",[401, {"Content-Type":"application/json; charset=utf-8"}, "NEED AUTH"]);

var tmp = $.ajax;
/*$.ajax = function(url, options){
    var result = tmp(url, options);
    fakeserver.respond();
    return result;
}*/
