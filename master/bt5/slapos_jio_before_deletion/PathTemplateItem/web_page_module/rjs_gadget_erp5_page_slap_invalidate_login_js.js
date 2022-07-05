/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

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
              return gadget.jio_putAttachment(doc.relative_url,
                url + doc.relative_url + "/ERP5Login_invalidate", {});
            });
        })
        .push(function () {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
            .push(function () {
              // Workaround, find a way to open document without break gadget.
              return gadget.redirect({"command": "change",
                                    "options": {jio_key: "/", "page": "slap_person_view"}});
            });
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Login is Disabled.",
          "Login to be disabled:",
          "Warning",
          "Ensure you have another login configured, else you will not be able to login anymore.",
          "Parent Relative Url",
          "Disable Login"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.getSetting("hateoas_url")
            .push(function () {
              return RSVP.all([
                gadget.getDeclaredGadget('form_view'),
                gadget.jio_get(options.jio_key),
                gadget.getTranslationList(translation_list)
              ]);
            });
        })
        .push(function (result) {
          options.doc = result[1];
          gadget.message_translation = result[2][0];
          page_title_translation = result[2][5];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": "",
                  "title": result[2][1] + " ",
                  "default": options.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference_label",
                  "hidden": 0,
                  "type": "StringField"
                },
                "message": {
                  "description": "",
                  "title": result[2][2],
                  "default": result[2][3],
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "title_label",
                  "hidden": 0,
                  "type": "StringField"
                },

                "my_relative_url": {
                  "description": "",
                  "title": result[2][4],
                  "default": options.jio_key,
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
                "left",
                [["my_title"], ["my_relative_url"]]
              ], [
                "bottom",
                [["message"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: false
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'})
          ]);
        })
        .push(function (result) {
          var header_dict = {
            selection_url: result[1],
            page_title: page_title_translation + ": " + options.doc.reference
          };
          header_dict.submit_action = true;
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));