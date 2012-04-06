$(function(){

    module("Instance & Computer Methods Tests", {
        setup: function(){
            this.server = sinon.sandbox.useFakeServer();
            this.header = {"Content-Type":"application/json; charset=utf-8"};
            this.error = [409, this.header, '']
            this.slap = new SlapOs();
        },
        tearDown: function(){
            this.server.restore();
        }
    });

    test("Requesting a new instance - Success Response", function(){
        expect(2);
        callback = this.spy();
        
        responseBody = [{instance_id: "anId",status: "started",connection: {}}];
        response = [201, this.header, JSON.stringify(responseBody)];
        this.server.respondWith("POST", "/request", response);
        
        data = '{"title": "My unique instance","software_release": "http://example.com/example.cfg","software_type": "type_provided_by_the_software","slave": False,"status": "started","sla": {"computer_id": "COMP-0"}';
        this.slap.newInstance(data, callback);
        this.server.respond();
        
        ok(callback.calledOnce, "callback call");
        ok(callback.calledWith(responseBody), 'callback check right parameters');
    });
    
    test("Requesting a new instance - Fail Response", function(){
        expect(1);
        callback = this.spy();
        
        this.server.respondWith("POST", "/request", this.error);
        
        data = '{"title": "My unique instance","software_release": "http://example.com/example.cfg","software_type": "type_provided_by_the_software","slave": False,"status": "started","sla": {"computer_id": "COMP-0"}';
        this.slap.newInstance(data, callback);
        this.server.respond();
        
        ok(!callback.calledOnce, "callback not call");
    });
    
    test("Deleting an instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [202, this.header, ''];
        this.server.respondWith("DELETE", /\/instance\/(\w+)/, response);
        
        this.slap.deleteInstance('id', callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Get instance information", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("GET", /\/instance\/(\w+)/, response);
        
        this.slap.getInstance('id', callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Get instance authentication certificates", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("GET", /\/instance\/(\w+)\/certificate/, response);
        
        this.slap.getInstanceCert('id', callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Bang instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("GET", /\/instance\/(\w+)\/bang/, response);
        
        data = '';
        this.slap.bangInstance('id', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Modifying instance", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("PUT", /\/instance\/(\w+)/, response);
        
        data = '';
        this.slap.editInstance('id', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Register a new computer", function(){
        expect(1);
        callback = this.spy();
        
        response = [201, this.header, ''];
        this.server.respondWith("POST", /\/computer/, response);
        
        data = '';
        this.slap.newComputer(data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Getting computer information", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("GET", /\/computer\/(\w+)/, response);
        
        data = '';
        this.slap.getComputer('id', callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Modifying computer", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("PUT", /\/computer\/(\w+)/, response);
        
        data = '';
        this.slap.editComputer('id', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Supplying new software", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/supply/, response);
        
        data = '';
        this.slap.newSoftware('computerId', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Bang computer", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/bang/, response);
        
        data = '';
        this.slap.bangComputer('id', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
    
    test("Report computer usage", function(){
        expect(1);
        callback = this.spy();
        
        response = [200, this.header, ''];
        this.server.respondWith("POST", /\/computer\/(\w+)\/report/, response);
        
        data = '';
        this.slap.newComputer('id', data, callback);
        this.server.respond();
        
        equal(1, this.server.requests.length, 'A request has been sent');
    });
});