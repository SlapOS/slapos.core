/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition('notifySubmit', function () {
      return this.triggerSubmit();
    })

    .onEvent('submit', function () {
      var gadget = this;
      return gadget.notifySubmitting()
        .push(function () {
          return gadget.getDeclaredGadget('form_view');
        })
        .push(function (form_gadget) {
          return form_gadget.getContent();
        })
        .push(function (doc) {
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              return gadget.jio_getAttachment(doc.relative_url,
                url + doc.relative_url +
                  "/SubscriptionRequestModule_requestSubscritption?default_email_text=" + encodeURIComponent(doc.default_email_text) +
                  "&name=" + encodeURIComponent(doc.name) +
                  "&amount=" + encodeURIComponent(doc.amount));
            });
        })
        .push(function (result) {
          return gadget.redirect({"command": "change",
                                  "options": {"jio_key": "/",
                                              "page": "slap_subscription_pre_payment",
                                              "subscription_request": result}});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this,
          subscription = options.subscription,
          payment = options.payment;
      return RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getSetting("hateoas_url")
          ]);
        })
        .push(function (result) {
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "your_payment_button": {
                  "description": "Proceed to Payment",
                  "title": "",
                  "default": {payment_url: result[1] + "/" + payment + "/PaymentTransaction_redirectToSubscriptionManualPayzenPayment"},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_erp5_page_slap_subscription_payment_button.html",
                  "sandbox": "",
                  "key": "payment_url",
                  "hidden": 0,
                  "type": "GadgetField"
                },
                "my_relative_url": {
                  "description": "",
                  "title": "Parent Relative Url",
                  "default": "subscription_request_module",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "relative_url",
                  "hidden": 1,
                  "type": "StringField"
                }
              }},
              "_links": {
                "type": {
                  // form_list display portal_type in header
                  name: ""
                }
              }
            },
            form_definition: {
              group_list: [[
                "bottom",
                [["your_payment_button"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updateHeader({
            page_title: "Please input your name and your email"
          });
        });
    });
}(window, rJS, RSVP));