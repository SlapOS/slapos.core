/*globals console, window, rJS, RSVP, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, domsugar) {
  "use strict";
  rJS(window)
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("updateHeader", "updateHeader")

    .declareMethod("render", function (options) {
      var gadget = this;

      return new RSVP.Queue()
        .push(function () {
          var message,
            advice,
            page_title;
          if (options.result === "success") {
            page_title = "Thank you for your Payment";
            message = "Thank you for finalising the payment.";
            advice = "It will be processed by PayZen interface.";
          } else if (options.result === "cancel") {
            page_title = "Payment cancelled";
            message = "You have cancelled the payment process.";
            advice = "Please consider continuing it as soon as possible, " +
              "otherwise you will be not able to use full functionality.";
          } else if (options.result === "error") {
            page_title = "Payment Error";
            message = "There was an error while processing the payment.";
            advice = "Please try again later or contact the support.";
          } else if (options.result === "referral") {
            page_title = "Payment Referral";
            message = "Your credit card was refused by payment system.";
            advice = "Please contact your bank or use another credit card.";
          } else if (options.result === "refused") {
            page_title = "Payment Refused";
            message = "The payment has been refused.";
            advice = "Please contact your bank.";
          } else if (options.result === "return") {
            page_title = "Payment Unfinished";
            message = "You have not finished your payment.";
            advice = "Please consider continuing it as soon as possible, " +
              "otherwise you will be not able to use full functionality.";
          } else if (options.result === "free") {
            page_title = "This payment is free";
            message = "You are trying to pay a Free invoice.";
            advice = "Please, contact us by opening a ticket " +
              "to ask more information.";
          } else if (options.result === "contact_us") {
            page_title = "Please, contact us";
            message = "You are trying to pay an invoice, " +
              "but the automatic payments are disabled currently.";
            advice = "Please contact us by opening a ticket with the " +
              "invoice information, we will provide you an " +
              "alternative way to pay.";
          } else if (options.result === "already_registered") {
            page_title = "Payment already registered";
            message = "Your payment had already been registered.";
          } else {
            throw new Error("Unknown action to take: " + options.result);
          }

          domsugar(gadget.element, {},
            [
              domsugar("p", {}, [
                domsugar("center", {}, [
                  domsugar("strong", {text: message})
                ])
              ]),
              domsugar("p", {}, [
                domsugar("center", {text: advice})
              ])
            ]);

          return RSVP.hash({
            page_title: page_title,
            page_icon: 'home',
            front_url: gadget.getUrlFor({command: 'display'})
          });
        })
        .push(function (hash) {
          return gadget.updateHeader(hash);
        });
    });
}(window, rJS, RSVP, domsugar));