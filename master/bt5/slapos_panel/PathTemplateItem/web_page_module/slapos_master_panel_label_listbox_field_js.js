/*globals window, document, rJS, JSON, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, document, rJS, JSON, domsugar) {
  "use strict";

  rJS(window)
    .declareMethod("getContent", function () {
      return {};
    })
    .declareMethod("render", function (options) {
      var gadget = this,
        a,
        pre,
        value = options.value,
        element = gadget.element;
      if (typeof value === "string") {
        if (value.startsWith("http://") ||
             value.startsWith("https://")) {
          domsugar(element, [
            domsugar('a', {
              href: value,
              target: '_blank',
              text: value
            })
          ]);
        // } else if (options.value.indexOf("\n") !== -1) {
        } else {
          domsugar(element, [
            domsugar('pre', {
              text: value
            })
          ]);
        }
      } else {
        domsugar(element, {
          text: JSON.stringify(value)
        });
      }
    });
}(window, document, rJS, JSON, domsugar));