/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    inline_source = gadget_klass.__template_element
                         .getElementById("inline-template")
                         .innerHTML,
    inline_template = Handlebars.compile(inline_source);

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////

    .declareMethod("render", function (options) {
      var gadget = this;
      gadget.options = options;
      return gadget.getElement()
       .push(function (element) {
          element.innerHTML = inline_template({
              url: options.value.url,
              text: options.value.text
            });
          return element;
        });
    });
}(window, rJS, RSVP, Handlebars));