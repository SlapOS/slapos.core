/*globals console, window, rJS, RSVP, domsugar */
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
                  // XXX Translation
                  text: translation_dict["Pay Now"],
                  href: gadget.state.hateoas_url + gadget.state.payment_transaction +
                    "/PaymentTransaction_redirectToManualSlapOSPayment"
                })
              ]);
          } else {
            link = domsugar("li", {"text": gadget.state.payment_transaction});
          }
          domsugar(gadget.element, {}, [
            domsugar("ul", {"class": "grid-items"}, [link])
          ]);
          return translation_dict;
        })
    })

    .declareMethod("render", function (options) {
      var gadget = this;
      return gadget.getSetting("hateoas_url")
        .push(function (hateoas_url) {
          // XXX RAFAEL this should comes from the options and not from a query like this.
          return gadget.jio_getAttachment(options.value.jio_key,
                hateoas_url +  options.value.jio_key +
                "/AccountingTransaction_getPaymentStateAsHateoas")
            .push(function (state) {
              return gadget.changeState({
                payment_transaction: state.payment_transaction,
                payment_state: state.state,
                hateoas_url: hateoas_url
              });
            });
        });
    });
}(window, rJS, domsugar));