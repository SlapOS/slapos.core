(function ($) {
  $.widget('mobile.panelcontainer', $.mobile.widget, {
    // Default options
    options: {},
    
    /* This method create the panelcontainer
     * its role is to prepare the webpage to display one or any panel(s)
     * This plugin will create panel html tags, per example:
     * <section data-role="panel" data-panel-name="login" ... ></section>
     * Once this plugin will finished its work, an event will be fire and catch by
     * the panel plugin
     * */
    _create: function () {
      // Trigger before create panelcontainer event
      //
      // [ ... ]
      //
      // Trigger after create panelcontainer event
    },

    // code snippet to sync options between this object and data-* attribute
    // it will be useful for keep html tag up to date when dynamically adding options
    _option: function (name, value) {
      var $el = this.element;
      if (value !== undefined) {
        this.options[name] = value;
        if (typeof value !== 'function') {
          $el[0].dataset[name] = value;
        }
      }
      return this.options[name] === undefined ? $el[0].dataset[name] : this.options[name];
    },

    /* public method to refresh the panelcontainer
     * the main purpose of this method is to bind it to resize event in order to 
     * react on window resizing event.
     * */
    refresh: function () {
    }
  });

  // This widget may contain all routing stuff and be bound to the haschange event
  // or be bound to pagecreate event in case of we want to separate routing process from
  // rendering process.
  $(document).bind('pagecreate', function (e) {
    // Call create method
  });

}(jQuery));
