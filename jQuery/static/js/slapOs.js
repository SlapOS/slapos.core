;(function($, window, document, undefined) {
    var SlapOs = function(elem, options){
        this.elem = elem;
        this.$elem = $(elem);
        this.options = options;
        this.metadata = this.$elem.data('plugin-options');
    };
    
    SlapOs.prototype = {
        defaults: {
            host: ''
        },
        
        init: function(){
            this.config = $.extend({}, this.defaults, this.options, this.metadata);
            this.store = Modernizr.localstorage ? this.lStore : this.cStore;
            this.store('host', this.config.host);
            return this;
        },
        
        /* Local storage method */
        lStore: function(name, value){
            if(Modernizr.localstorage)
                return value == undefined ? window.localStorage[name] : window.localStorage[name] = value;
            return false;
        },
        
        /* Cookie storage method */
        cStore: function(name, value){
            if(value != undefined){
                document.cookie = name+"="+value+";domain="+window.location.hostname+";path="+window.location.pathname;
            }else{
                var i,x,y, cookies = document.cookie.split(';');
                for(i=0; i<cookies.length; i++){
                    x = cookies[i].substr(0, cookies[i].indexOf('='));
                    y = cookies[i].substr(cookies[i].indexOf('=')+1);
                    x=x.replace(/^\s+|\s+$/g,"");
                    if(x == name) return unescape(y);
                }
            }
        },
        
        request: function(type, url, callback, data){
            data = data || '';
            return $.ajax({
                url: this.store('host')+url,
                dataType: 'json',
                data: data,
                context: this.$elem,
                type: type,
                statusCode: {
                    0: function(){ console.log('status code 0') }
                }
            }).done(callback).fail(this.failCallback);
        },
        
        failCallback: function(jqXHR, textStatus){
            //console.log(jqXHR);
        },
        
        newInstance: function(data, callback){
            return this.request('POST', '/request', callback, data);
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

})(jQuery, window , document);