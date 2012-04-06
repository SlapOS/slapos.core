(function(window, $) {
    var SlapOs = function(elem, options){
        this.elem = elem;
        this.$elem = $(elem);
        this.options = options;
        this.metadata = this.$elem.data('plugin-options');
    };
    
    SlapOs.prototype = {
        host: '',
        
        init: function(){
            this.config = $.extends({}, this.defaults, this.options, this.metadata);
            return this;
        },
        
        request: function(type, url, callback, data){
            data = data || '';
            return $.ajax({
                url: this.host+url,
                dataType: 'json',
                data: data,
                type: type,
                statusCode: {
                    409: function(){console.log('Status Code : 409')},
                },
                success: function(data){ callback(data); }
            });
        },
        
        newInstance: function(data, callback){
            this.request('POST', '/request', callback, data);
        },
        
        deleteInstance: function(id, callback){
            this.request('DELETE', '/instance/'+id, callback);
        },
        
        getInstance: function(id, callback){
            this.request('GET', '/instance/'+id, callback);
        },
        
        getInstanceCert: function(id, callback){
            this.request('GET', '/instance/'+id+'/certificate', callback);
        },
        
        bangInstance: function(id, log, callback){
            this.request('POST', '/instance/'+id+'/bang', callback, log);
        },
        
        editInstance: function(id, data, callback){
            this.request('PUT', '/instance/'+id, callback, data);
        },
        
        newComputer: function(data, callback){
            this.request('POST', '/computer', callback, data);
        },
        
        getComputer: function(id, callback){
            this.request('GET', '/computer/'+id, callback, data);
        },
        
        editComputer: function(id, data, callback){
            this.request('PUT', '/computer/'+id, callback, data);
        },
        
        newSoftware: function(computerId, data, callback){
            this.request('POST', '/computer/'+computerId+'/supply', callback, data);
        },
        
        bangComputer: function(id, log, callback){
            this.request('POST', '/computer/'+id+'/bang', callback, log);
        },
        
        computerReport: function(id, data, callback){
            this.request('POST', '/computer/'+id+'/report', callback, data);
        }
    };
    
    $.fn.slapos = function(options){
        return this.each(function(){
            new SlapOs(this, options).init();
        });
    };
    
    window.SlapOs = SlapOs;
})(window, jQuery);