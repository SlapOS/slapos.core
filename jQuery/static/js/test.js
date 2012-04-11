$(function(){

    var h = getParameterByName("login");
    var slap = new SlapOs(document, {host: h}).init();

    module("Ajax Tests", {
        setup: function(){
            this.server = sinon.sandbox.useFakeServer();
            this.header = {"Content-Type":"application/json; charset=utf-8"};
            this.error = [409, this.header, 'ERROR'];
        },
        teardown: function(){
            this.server.restore();
        }
    });

    test("Requesting a new instance", function(){
        expect(2);
        callback = this.spy();
    
        responseBody = [{instance_id: "anId",status: "started",connection: {}}];
        response = [201, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("POST", "/request", response);
        
        slap.newInstance('', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
        ok(callback.calledWith(responseBody), 'should return mainly id and status of an instance');
    });
    
    test("Requesting a new instance - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", "/request", this.error);
        
        slap.newInstance('', callback);
        this.server.respond();

        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Deleting an instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [202, this.header, ''];
        this.server.respondWith("DELETE", /\/instance\/(\w+)/, response);
        
        slap.deleteInstance('id', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });

    test("Deleting an instance - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("DELETE", /\/instance\/(\w+)/, this.error);
        
        slap.deleteInstance('id', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Get instance information", function(){
        expect(2);
        callback = this.spy();
        
        responseBody = [{instance_id: "anId", status: "start", software_release: "http://example.com/example.cfg",
                        software_type: "type_provided_by_the_software", slave: "False", connection: {
                            custom_connection_parameter_1: "foo",
                            custom_connection_parameter_2: "bar"},
                        parameter: {Custom1: "one string", Custom2: "one float",
                                    Custom3: ["abc", "def"],},
                        sla: {computer_id: "COMP-0",},
                        children_id_list: ["subinstance1", "subinstance2"],
                        partition: {public_ip: ["::1", "91.121.63.94"], private_ip: ["127.0.0.1"],
                                    tap_interface: "tap2",},}];
        response = [200, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("GET", /\/instance\/(\w+)/, response);
        
        slap.getInstance('id', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be call");
        ok(callback.calledWith(responseBody), "should return informations of an instance");
    });

    test("Get instance information - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("GET", /\/instance\/(\w+)/, this.error);
        
        slap.getInstance('id', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });

    test("Get instance authentication certificates", function(){
        expect(2);
        callback = this.spy();
        
        responseBody = [{ ssl_key: "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADAN...h2VSZRlSN\n-----END PRIVATE KEY-----",
                          ssl_certificate: "-----BEGIN CERTIFICATE-----\nMIIEAzCCAuugAwIBAgICHQI...ulYdXJabLOeCOA=\n-----END CERTIFICATE-----",}];
        response = [200, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("GET", /\/instance\/(\w+)\/certificate/, response);
        
        slap.getInstanceCert('id', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback call");
        ok(callback.calledWith(responseBody));
    });

    test("Get instance authentication certificates - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("GET", /\/instance\/(\w+)\/certificate/, this.error);
        
        slap.getInstanceCert('id', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Bang instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/instance\/(\w+)\/bang/, response);
        
        data = '';
        slap.bangInstance('id', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });

    test("Bang instance - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", /\/instance\/(\w+)\/bang/, this.error);
        
        slap.bangInstance('id', data, callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Modifying instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("PUT", /\/instance\/(\w+)/, response);
        
        data = '';
        slap.editInstance('id', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });

    test("Modifying instance - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("PUT", /\/instance\/(\w+)/, this.error);
        
        slap.editInstance('id', '', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Register a new computer", function(){
        expect(2);
        callback = this.spy();
        
        responseBody = [{computer_id: "COMP-0",
                        ssl_key: "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADAN...h2VSZRlSN\n-----END PRIVATE KEY-----",
                        ssl_certificate: "-----BEGIN CERTIFICATE-----\nMIIEAzCCAuugAwIBAgICHQI...ulYdXJabLOeCOA=\n-----END CERTIFICATE-----",}];
        response = [201, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("POST", "/computer", response);
        
        slap.newComputer('', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
        ok(callback.calledWith(responseBody), "should return a computerID, ssl key and ssl certificates");
    });

    test("Register a new computer - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", "/computer", this.error);
        
        slap.newComputer('', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Getting computer information", function(){
        expect(2);
        callback = this.spy();
        
        responseBody = [{computer_id: "COMP-0",
                        software: [{software_release: "http://example.com/example.cfg",
                                   status: "install"},],
                        partition: [{title: "slapart1",instance_id: "foo",status: "start",
                                     software_release: "http://example.com/example.cfg"},
                                    {title: "slapart2",instance_id: "bar",status: "stop",
                                     software_release: "http://example.com/example.cfg"},],}];
        response = [200, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("GET", /\/computer\/(\w+)/, response);
        
        slap.getComputer('id', callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
        ok(callback.calledWith(responseBody), "should return informations of a computer");
    });

    test("Getting computer information - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("GET", /\/computer\/(\w+)/, this.error);
        
        slap.getComputer('id', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Modifying computer", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("PUT", /\/computer\/(\w+)/, response);
        
        data = '';
        slap.editComputer('id', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });
    
    test("Modifying computer - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("PUT", /\/computer\/(\w+)/, this.error);
        
        slap.editComputer('id', '', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });

    test("Supplying new software", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/supply/, response);
        
        data = '';
        slap.newSoftware('computerId', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });

    test("Supplying new software - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", /\/computer\/(\w+)\/supply/, this.error);
        
        slap.newSoftware('computerId', '', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Bang computer", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/bang/, response);
        
        data = '';
        slap.bangComputer('id', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback should be called");
    });

    test("Bang computer - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", /\/computer\/(\w+)\/bang/, this.error);
        
        slap.bangComputer('id', '', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    test("Report computer usage", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/report/, response);
        
        data = '';
        slap.computerReport('id', data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback call");
    });
    
    test("Report computer usage - Fail", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", /\/computer\/(\w+)\/report/, this.error);
        
        slap.computerReport('id', '', callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback should not be called");
    });
    
    module("Common Tests");
    
    test("Check if host has been saved", function(){
        newS = new SlapOs(document, {host: "http://foo.com"}).init();
        equal(newS.store('host'), "http://foo.com", "should contains host whatever is the method")
    });
    
    test("Modifying host after initialisation at start", function(){
        newS = new SlapOs(document, {host: "http://foo.com"}).init();
        newS.store('host', 'http://examples.com');
        equal(newS.store('host'), "http://examples.com", "should contains modified host")
    });
});

function getParameterByName(name){
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.search);
    if(results == null) return "";
    else return decodeURIComponent(results[1].replace(/\+/g, " "));
}