/*globals window, document, rJS, JSON */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, document, rJS, JSON) {
  "use strict";

  rJS(window)
    .declareMethod("getContent", function () {
      return {};
    })
    .declareMethod("render", function (options) {
      var gadget = this, a, pre, value;
      return gadget.getElement()
        .push(function (element) {
          value = options.value;
          if (typeof options.value === "string") {
            if (options.value.startsWith("http://") ||
                 options.value.startsWith("https://")) {
              a = document.createElement('a');
              a.setAttribute("href", options.value);
              a.setAttribute("target", "_blank");
              a.innerText = options.value;
              value = a.outerHTML;
            } else if (options.value.indexOf("\n") !== -1) {
              pre = document.createElement('pre');
              pre.innerText = options.value;
              value = pre.outerHTML;
            }
            element.innerHTML = value;
          } else {
            element.innerHTML = JSON.stringify(value);
          }
          return element;
        });
    });
}(window, document, rJS, JSON));