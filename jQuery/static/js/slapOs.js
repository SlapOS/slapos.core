;(function($) {
    var methods = {
        defaults: {
            host: ''
        },
        
        init: function( options ){
            var settings = $.extend({
                'host': ''
            }, options);

            return this.each(function(){
                methods['store'] = Modernizr.localstorage ? methods.lStore : methods.cStore;
                $(this).slapos('store', 'host', settings.host);
            });
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

        statusDefault: function(){
            return {
                0: function(){ console.error("status error code: 0"); },
                404: function(){ console.error("status error code: Not Found !"); }
            }
        },
        
        request: function(type, url, callback, statusEvent, data){
            data = data || '';
            statusEvent = statusEvent || this.statusDefault;
            return this.each(function(){
                $.ajax({
                    url: methods.store('host')+url,
                    dataType: 'json',
                    data: data,
                    context: $(this),
                    type: type,
                    statusCode: statusEvent,
                    success: callback
                });
            });
        },
        
        newInstance: function(data, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/request', callback, statusEvent, data);
        },
        
        deleteInstance: function(id, callback, statusEvent){
            return $(this).slapos('request', 'DELETE', '/instance/'+id, callback, statusEvent);
        },
        
        getInstance: function(id, callback, statusEvent){
            return $(this).slapos('request', 'GET', '/instance/'+id, callback, statusEvent);
        },
        
        getInstanceCert: function(id, callback, statusEvent){
            return $(this).slapos('request', 'GET', '/instance/'+id+'/certificate', callback, statusEvent);
        },
        
        bangInstance: function(id, log, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/instance/'+id+'/bang', callback, statusEvent, log);
        },
        
        editInstance: function(id, data, callback, statusEvent){
            return $(this).slapos('request', 'PUT', '/instance/'+id, callback, statusEvent, data);
        },
        
        newComputer: function(data, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/computer', callback, statusEvent, data);
        },
        
        getComputer: function(id, callback, statusEvent){
            return $(this).slapos('request', 'GET', '/computer/'+id, callback, statusEvent);
        },
        
        editComputer: function(id, data, callback, statusEvent){
            return $(this).slapos('request', 'PUT', '/computer/'+id, callback, statusEvent, data);
        },
        
        newSoftware: function(computerId, data, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/computer/'+computerId+'/supply', callback, statusEvent, data);
        },
        
        bangComputer: function(id, log, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/computer/'+id+'/bang', callback, statusEvent, log);
        },
        
        computerReport: function(id, data, callback, statusEvent){
            return $(this).slapos('request', 'POST', '/computer/'+id+'/report', callback, statusEvent, data);
        }
    };
    
    $.fn.slapos = function(method){
        if ( methods[method] ) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.slapos' );
        }
    };
})(jQuery);