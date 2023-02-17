/*globals console, window, rJS, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, domsugar) {
  "use strict";

  rJS(window)
    .declareMethod("getContent", function () {
      return {};
    })

    .onStateChange(function () {
      var gadget = this,
        annotated_message = "",
        annotated_template_id,
        div = gadget.element.querySelector('div.annotated_help')
      if (gadget.state.template_id === undefined) {
        // Verify if template-id is present on the div element
        annotated_template_id = gadget.element.getAttribute("data-template-id");
        if (annotated_template_id === "add-new-login-header-text") {
          annotated_message = domsugar('detatils', {}, [
            domsugar('summary', {text: 'Password Policy'}),
            domsugar('ul', {}, [
              domsugar('li', {text: 'Minimum 7 characters in length'}),
              domsugar('li', {text: 'At least one Uppercase Letter'}),
              domsugar('li', {text: 'At least one Lowercase Letter'}),
              domsugar('li', {text: 'At least one Number (0 to 9)'}),
              domsugar('li', {text: 'At least one Symbol out of $!:;_- .'})
            ]),
            domsugar('p'),
            domsugar('p')
          ]);
        }
      }

      return domsugar(div, {class: 'annotated_help'}, [annotated_message]);
    })

    .declareMethod("render", function (options) {
      var gadget = this;
      return gadget.changeState({
        template_id: options.template_id
      });
    });
}(window, rJS, domsugar));