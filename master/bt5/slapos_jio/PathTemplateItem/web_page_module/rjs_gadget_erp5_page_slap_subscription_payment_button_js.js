/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    inline_payment_source = gadget_klass.__template_element
                         .getElementById("inline-payment-template")
                         .innerHTML,
    inline_payment_template = Handlebars.compile(inline_payment_source);

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
          element.innerHTML = inline_payment_template({
              payment_url: options.value.payment_url
            });
          return element;
        });
    });
}(window, rJS, RSVP, Handlebars));