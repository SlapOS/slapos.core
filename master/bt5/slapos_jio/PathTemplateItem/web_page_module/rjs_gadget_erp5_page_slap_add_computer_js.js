/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
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
              // This is horrible
              return gadget.jio_getAttachment(doc.parent_relative_url,
                url + doc.parent_relative_url + "/Person_requestComputer?title=" + doc.title);
            });
        })
        .push(function (result) {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
            .push(function () {
              return gadget.render(result);
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
          "New Computer created.",
          "The name of a document in ERP5",
          "Title",
          "Reference",
          "Link to the Computer",
          "Your Certificate",
          "Your Key",
          "Parent Relative Url",
          "New Computer"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getUrlFor({command: "change",
                              options: { jio_key: options.relative_url, page: "slap_controller"}}),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[2][0];
          page_title_translation = result[2][8];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[2][1],
                  "title": result[2][2],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "title",
                  "hidden": (options.certificate === undefined) ? 0 : 1,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": result[2][1],
                  "title": result[2][3],
                  "default": options.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": (options.reference === undefined) ? 1 : 0,
                  "type": "StringField"
                },
                "my_computer_url": {
                  "description": "",
                  "title": result[2][4],
                  "default": "<a href=" + result[1] + "> Click here to access your computer </a>",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "computer_url",
                  "hidden": (options.certificate === undefined) ? 1 : 0,
                  "type": "EditorField"
                },
                "my_certificate": {
                  "description": "",
                  "title": result[2][5],
                  "default": options.certificate,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "certificate",
                  "hidden": (options.certificate === undefined) ? 1 : 0,
                  "type": "TextAreaField"
                },
                "my_key": {
                  "description": "",
                  "title": result[2][6],
                  "default": options.key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "key",
                  "hidden": (options.key === undefined) ? 1 : 0,
                  "type": "TextAreaField"
                },
                "my_parent_relative_url": {
                  "description": "",
                  "title": result[2][7],
                  "default": "computer_module",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "parent_relative_url",
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
                [["my_title"], ["my_parent_relative_url"]]
              ], [
                "center",
                [["my_key"], ["my_certificate"]]
              ], [
                "bottom",
                [["my_computer_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'change', options: {page: "slap_computer_list"}})
          ]);
        })
        .push(function (url_list) {
          return gadget.updateHeader({
            page_title: page_title_translation,
            selection_url: url_list[0],
            submit_action: true
          });
        });
    });
}(window, rJS, RSVP));