/*globals console, window, rJS, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, domsugar) {
  "use strict";
  rJS(window)
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationDict", "getTranslationDict")

    .declareMethod("getContent", function () {
      return {};
    })
    .onStateChange(function () {
      var gadget = this,
        link;
      return gadget.getTranslationDict(['Pay Now'])
        .push(function (translation_dict) {
          if (gadget.state.payment_transaction !== null) {
            link = domsugar("li", {},
              [
                domsugar("a", {
                  class: "ui-btn ui-first-child ui-btn-icon-center",
                  text: translation_dict["Pay Now"],
                  href: gadget.state.hateoas_url +
                    gadget.state.payment_transaction +
                    "/PaymentTransaction_redirectToManualSlapOSPayment"
                })
              ]);
          } else {
            link = domsugar("li", {"text": gadget.state.payment_state});
          }
          domsugar(gadget.element, {}, [
            domsugar("ul", {"class": "grid-items"}, [link])
          ]);
          return translation_dict;
        });
    })

    .declareMethod("render", function (options) {
      var gadget = this;
      return gadget.getSetting("hateoas_url")
        .push(function (hateoas_url) {
          return gadget.changeState({
            payment_transaction: options.value.payment_transaction,
            payment_state: options.value.state,
            hateoas_url: hateoas_url
          });
        });
    });
}(window, rJS, domsugar));