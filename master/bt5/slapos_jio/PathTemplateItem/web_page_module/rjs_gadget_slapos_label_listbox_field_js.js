/*globals console, window, document, rJS, loopEventListener, i18n */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, document, rJS) {
  "use strict";
  var gadget_klass = rJS(window);

  gadget_klass
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translateHtml", "translateHtml")

    .declareMethod("getContent", function () {
      return {};
    })
    .declareMethod("render", function (options) {
      var gadget = this, a, pre, value;
      return gadget.getElement()
        .push(function (element) {
          value = options.value;
          if (options.value) {
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
          }
          element.innerHTML = value;
          return element;
        });
    });
}(window, document, rJS));