/**
 * NEXEDI
 * Author: Thomas Lechauve
 * Date: 4/24/12
 */


var o = [];
;(function($){


	$.keysName = { "down": 40, "up": 38, "tab": 9 };
	var selectors = "a, input";

	var methods = {
		init: function(key){
			if( key == undefined ) {
				$(this).addClass("shortcutable");
				o.push($(this)[0]);
				return $(this).shortcuts('list');
			} else {
				return $(this).shortcuts('bindKey', key);
			}
		},

		bindKey: function(key){
			return this.each(function(){
				var $this = $(this);
				$(document).bind('keydown', function(e){
					if( e.keyCode == ($.isNumeric(key) ? key : $.keysName[key]) ) {
						e.preventDefault();
						$this.focus();
					}
				});
			});
		},

		list: function(){
			return this.each(function(){
				$(this).bind('keydown', function(e){
					if( e.keyCode == $.keysName["down"] ){
						$(this).shortcuts('nextChild');
					} else if (e.keyCode == $.keysName["up"] ){
						$(this).shortcuts('prevChild');
					} else if (e.keyCode == $.keysName["tab"] ) {
						e.preventDefault();
						if ( e.shiftKey ) {
							$(this).shortcuts('prev').find(selectors).first().focus();
						} else {
							$(this).shortcuts('next').find(selectors).first().focus();
						}
					}
				});
				$(this).find('a').first().focus().select();
			});
		},

		nextChild: function(){
			return this.each(function(){
				if( $(document.activeElement).parents('.shortcutable').is(':last-child') ) {
					$(document.activeElement).grandma().find(selectors).first().focus();
				} else {
					$(document.activeElement).parent().next().find(selectors).focus();
				}
			});
		},

		prevChild: function(){
			return this.each(function(){
				if( $(document.activeElement).parent().is(':first-child') ) {
					$(document.activeElement).grandma().find(selectors).last().focus();
				} else {
					$(document.activeElement).parent().prev().find(selectors).focus();
				}
			});
		},

		next: function(){
			return $(o[($.inArray( $(this)[0], o) + 1 ) % o.length]);
		},

		prev: function(){
			var i = $.inArray($(this)[0], o);
			return $( o[ ( i <= 0 ? o.length - 1 : i - 1 )]);
		}
	};

	$.fn.shortcuts = function(method){
		if ( methods[method] ) {
			return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
		} else if ( typeof method === 'object' || ! method || $.isNumeric(method)) {
			return methods.init.apply( this, arguments );
		} else {
			$.error( 'Method ' +  method + ' does not exist on jQuery.shortcuts' );
		}
	};

	$.fn.grandma = function(){
		var e = this.parent().parent();
		return this.pushStack( e.get() );
	};
})(jQuery);
