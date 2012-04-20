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
                    else if(d.route == "disp") { self.form('displayData'); }
                });
            });
        },

        displayData: function(){
            $(this).html("<p>Ajax loading ...</p>")
                .slapos('getInstance', '200', function(data){
                    $(this).html(JSON.stringify(data));
                });
        },

        displayForm: function() {
            var form = '' +
                '<form>' +
                '<input type="text"/>' +
                '<input type="submit" value="Add"/>' +
                '</form>';
            $(this).html(form);

            $(this).find("form").submit(function(){
                $.redirect({route:'disp'});
                return false;
            });
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

$("section").form();
