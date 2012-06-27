jQuery(function(){

        var response, responseBody, url, data;


        module("Cross-domain Tests");
        test("200 response", function(){
            expect(1);
            stop(1);
            jQuery.ajax({
                url: 'http://sheldy.com:5000/200',
                complete: function() { start(); },
                statusCode: {
                    200: function(){ ok(true, "should get 200 status");}
                }
            });
        });

        test("404 response", function(){
            expect(1);
            stop(1);
            jQuery.ajax({
                url: 'http://sheldy.com:5000/request',
                complete: function() { start(); },
                statusCode: {
                    404: function(xhr){
                        ok(true, "should get 404 error status status="+xhr.status);
                    },
                    0: function(){
                        ok(false, "should get 404 not but receive 0");
                    }
                }});
        });

        module("Storage Test", {
            setup: function() {
                this.myhost = 'http://www.example.com/api';
                jQuery(document).slapos({'host': this.myhost});
            }
        });

        test("", function() {
            expect(5);
            var test = "testValue",
                newToken = "newToken",
                nnToken = "";
            
            equal(this.myhost, jQuery(document).slapos('host'), "should contain the same host when initialized");
            
            jQuery(document).slapos('store', 'test', test);
            equal(test, window.localStorage.test, 'should add new key "test" in local storage');

            jQuery(document).slapos('access_token', newToken);
            equal(newToken, window.localStorage.access_token, 'should add new key "access_token" by using its shortcut method');

            nnToken = jQuery(document).slapos('access_token');
            equal(nnToken, newToken, 'should put "newToken" value in nnToken')

            jQuery(document).slapos('deleteStore', 'access_token');
            ok(window.localStorage.getItem('access_token') === null, 'should delete "access_token" from localStorage');
        });

        module("Callback Tests", {
            setup: function(){
                this.server = sinon.sandbox.useFakeServer();
                this.header = {"Content-Type":"application/json"};

                // Discovery response
                var discoBody = {
                    "request_instance": {
                      "authentication": true,
                      "url": "/request_instance",
                      "method": "POST",
                      "required": {
                         "status": "unicode",
                         "slave": "bool",
                         "title": "unicode",
                         "software_release": "unicode",
                         "software_type": "unicode",
                         "parameter": "object",
                         "sla": "object"
                      },
                      "optional": {}
                    }
                };
                var discoResponse = [200, this.header, JSON.stringify(discoBody)];
                this.server.respondWith("GET", '/api', discoResponse);
               
                // Error responses 
                this.bad_request = [400, this.header, 'Bad Request'];
                this.unauthorized = [401, this.header, 'Unauthorized'];
                this.payment = [402, this.header, 'Payment required'];
                this.not_found = [404, this.header, 'Not found'];
                this.server_error = [500, this.header, 'Internal server error'];
                
                jQuery(document).slapos({'host': '/api'});
            },
            teardown: function(){
                this.server.restore();
            }
        });

        test("Bad request", function(){
            expect(1);
            
            this.server.respondWith("POST", "/request_instance", this.bad_request);
            var callback = function(){
                ok(true, "should use 400 callback");
            },
            statusCode = {
                400: callback
            };
            var i = jQuery(document).slapos('instanceRequest', {
                url: "/request_instance",
                statusCode: statusCode,
                complete: function () { start() }
            });
            this.server.respond();
        });
        
        test("Unauthorized", function(){
            expect(1);
            
            this.server.respondWith("POST", "/request_instance", this.unauthorized);
            var callback = function(){
                ok(true, "should use 401 callback");
            },
            statusCode = {
                401: callback
            };
            jQuery(document).slapos('instanceRequest', {
                url: "/request_instance",
                statusCode: statusCode,
                complete: function () { start() }
            });
            this.server.respond();
        });
        
        test("Payment required", function(){
            expect(1);
            
            this.server.respondWith("POST", "/request_instance", this.payment);
            var callback = function(){
                ok(true, "should use 402 callback");
            },
            statusCode = {
                402: callback
            };
            jQuery(document).slapos('instanceRequest', {
                url: "/request_instance",
                statusCode: statusCode,
                complete: function () { start() }
            });
            this.server.respond();
        });
        
        test("Not found", function(){
            expect(1);
            
            this.server.respondWith("POST", "/request_instance", this.not_found);
            var callback = function(){
                ok(true, "should use 404 callback");
            },
            statusCode = {
                404: callback
            };
            jQuery(document).slapos('instanceRequest', {
                url: "/request_instance",
                statusCode: statusCode,
                complete: function () { start() }
            });
            this.server.respond();
        });
        
        test("Internal server error", function(){
            expect(1);
            
            this.server.respondWith("POST", "/request_instance", this.server_error);
            var callback = function(){
                ok(true, "should use 500 callback");
            },
            statusCode = {
                500: callback
            };
            jQuery(document).slapos('instanceRequest', {
                url: "/request_instance",
                statusCode: statusCode,
                complete: function () { start() }
            });
            this.server.respond();
        });
});
