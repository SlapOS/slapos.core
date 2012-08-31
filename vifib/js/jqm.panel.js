(function ($) {
  $.widget('mobile.panel', $.mobile.widget, {
    // Default options
    options: {},
    
    /* This method create the panel
     * it should fetch all information needed from html data-* attributes.
     * per example data-panel-template could contain id of a template define
     * in a script tag (see ICanHaz library)
     * */
    _create: function () {
      // Trigger before create panel event
      //
      // [ ... ]
      //
      // Trigger after create panel event
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

    /* public method to refresh the panel
    /* Update a panel should refresh information inside itself
     * without refreshing the entire webpage
     * */
    refresh: function () {
    }
  });

  // This widget is bound to panelcontainer create event to init itself
  $(document).bind('panelcontainercreate', function (e) {
    // Call create metho
  });

}(jQuery));
