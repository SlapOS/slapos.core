/*globals console, window, rJS, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, domsugar) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")

    .declareMethod("getContent", function () {
      return {};
    })
    .onStateChange(function () {
      var gadget = this;
      return gadget.getSetting("hateoas_url")
        .push(function (hateoas_url) {
          var link = hateoas_url + "/" +
                     gadget.state.jio_key +
                       "/SaleInvoiceTransaction_viewSlapOSPrintout";
          return domsugar(gadget.element, {}, [
            domsugar('ul', {class : 'grid-items'}, [
              domsugar('li', {}, [
                domsugar('a',
                  {
                    class: "ui-btn ui-first-child ui-btn-icon-center",
                    target: "_blank",
                    href: link
                  }, [
                    domsugar("img", {src: 'pdf_icon.png'})
                  ])
              ])
            ])
          ]);
        });
    })
    .declareMethod("render", function (options) {
      var gadget = this;
      return gadget.changeState({
        jio_key: options.value.jio_key
      });
    });
}(window, rJS, domsugar));