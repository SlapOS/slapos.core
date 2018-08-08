/*global window, rJS, RSVP, URL */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, URL) {
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
    .declareAcquiredMethod("jio_get", "jio_get")
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
                  "&subscription_reference=" + encodeURIComponent(doc.reference) +
                  "&name=" + encodeURIComponent(doc.name) +
                  "&amount=" + encodeURIComponent(doc.amount));
            });
        })
        .push(function (result) {
          var subscription = result.subscription,
              payment = result.payment;
          return gadget.redirect({"command": "change",
                                  "options": {"jio_key": "/",
                                              "page": "slap_subscription_pre_payment",
                                              "subscription": subscription,
                                              "payment": payment}});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this;
      return RSVP.Queue()
        .push(function () {
          return gadget.getSetting("me");
        })
        .push(function (me) {
          var promise_list = [];
          promise_list.push(gadget.getDeclaredGadget('form_view'));
          promise_list.push(gadget.getSetting('hateoas_url'));
          promise_list.push(gadget.getUrlFor(
            {command: "login", options: {}}));
          promise_list.push(gadget.getUrlFor(
            {command: "display", options: {page: "logout"}}));
          if (me !== undefined) {
            promise_list.push(gadget.jio_get(me));
          }
          return RSVP.all(promise_list);
        })
        .push(function (result) {
          var is_anonymous = result.length === 4,
              site_root_url = new URL(window.location.href).href,
              hateoas_url = result[1],
              full_name = is_anonymous ? "" : result[4].first_name + " " + result[4].last_name;
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "your_login_message": {
                  "description": "Login",
                  "title": "",
                  "default": "If you have login, you can login before continue. The reservation will be attached to your account.",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "login_message",
                  "hidden": is_anonymous ? 0 : 1,
                  "type": "StringField"
                },
                "your_login_button": {
                  "description": "Click to Login",
                  "title": "",
                  "default": { text: "Login",
                               url: hateoas_url + "/connection/login_form?allow_subscription=0&came_from=" + encodeURIComponent(site_root_url + result[2])},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_erp5_page_slap_subscription_button.html",
                  "sandbox": "",
                  "key": "login_url",
                  "hidden": is_anonymous ? 0 : 1,
                  "type": "GadgetField"
                },
                "your_subscribe_message": {
                  "description": "Subscribe",
                  "title": "",
                  "default": "Or if you don't have an account, fill this form. One account will be created for you in the end of the reservation process.",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "subscription_message",
                  "hidden": is_anonymous ? 0 : 1,
                  "type": "StringField"
                },
                "my_name": {
                  "description": "Your Name",
                  "title": "Name",
                  "default": full_name,
                  "css_class": "",
                  "required": 1,
                  "editable": is_anonymous,
                  "key": "name",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_email": {
                  "description": "",
                  "title": "Email",
                  "default": is_anonymous ? "" : result[4].default_email_text,
                  "css_class": "",
                  "required": 1,
                  "editable": is_anonymous,
                  "key": "default_email_text",
                  "hidden": 0,
                  "type": "EmailField"
                },
                "my_reference": {
                  "description": "",
                  "title": "Reference",
                  "default": options.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "reference",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_amount": {
                  "description": "",
                  "title": "Amount of VMs",
                  "default": options.amount,
                  "css_class": "",
                  "items": [["0", "0"], ["1", "1"], ["2", "2"], ["3", "3"],
                            ["4", "4"], ["5", "5"], ["6", "6"], ["7", "7"],
                            ["8", "8"], ["9", "9"], ["10", "10"]],
                  "required": 1,
                  "editable": 1,
                  "key": "amount",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_price": {
                  "description": "",
                  "title": "Price per VM",
                  "default": "19.95 €",
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "price",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_logout_message": {
                  "description": "Logout",
                  "title": "",
                  "default": "You are already logged in as as " + full_name + ". If you want to subscribe with another user, you can logout with the link below.",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "logout_message",
                  "hidden": is_anonymous ? 1 : 0,
                  "type": "StringField"
                },
                "your_logout_button": {
                  "description": "Click to Logout",
                  "title": "",
                  "default": {text: "Logout",
                              url: result[3]},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_erp5_page_slap_subscription_button.html",
                  "sandbox": "",
                  "key": "logout_url",
                  "hidden": is_anonymous ? 1 : 0,
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
                "center",
                [["your_login_message"], ["your_login_button"], ["your_subscribe_message"], ["my_name"], ["my_email"], ["my_amount"], ["my_price"], ["my_reference"], ["my_relative_url"]]
              ], [
                "bottom",
                [["your_logout_message"], ["your_logout_button"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updateHeader({
            page_title: "Please input your name and your email",
            submit_action: true
          });
        });
    });
}(window, rJS, RSVP, URL));