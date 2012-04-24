/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/17/12
 */
;(function($) {
    var methods = {
        init: function() {
            // Initialize slapos in this context
            $(this).slapos({host: ''});

            // Bind to urlChange event
            return this.each(function(){
                var self = $(this);
                $.subscribe("urlChange", function(e, d){
                    if(d.route == "form") { self.form('displayForm'); }
                    else if(d.route == "service" && d.id) { self.form('displayData', d.id); }
                });
            });
        },

        displayData: function(id){
            $(this).html("<p>Ajax loading...</p>")
                .slapos('getInstance', id, function(data){
                    $(this).form('render', 'service', data);
                }, {408: function(){ $(this).form('render', 'service-error', {id:id})}});
        },

        displayForm: function() {
            $(this).form('render', 'simple-form');

            $(this).find("form").submit(function(){
                $.redirect({route:'disp', id:$(this).find("input:text").val()});
                return false;
            });
        },

        render: function(template, data){
            $(this).html(ich[template](data, true));
        }
    };

    $.fn.form = function(method){
        if ( methods[method] ) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.form' );
        }
    };
})(jQuery);

$("#main").form();
