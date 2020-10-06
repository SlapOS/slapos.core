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
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition('notifySubmit', function () {
      return this.triggerSubmit();
    })

    .onEvent('submit', function () {
      var gadget = this;
      return gadget.getDeclaredGadget('form_view')
        .push(function (form_gadget) {
          return form_gadget.getContent();
        })
        .push(function (doc) {
          return gadget.jio_post(doc);
        })
        .push(function () {
          return gadget.redirect({"command": "change",
                                  "options": {"jio_key": gadget.state.jio_key,
                                              "page": "slap_controller"}});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "The name of a document in ERP5",
          "Title",
          "Include your message",
          "Your Message",
          "Source",
          "Follow up",
          "Portal Type",
          "Web Message",
          "Parent Relative Url",
          "New Message"
        ];
      gadget.state.jio_key = options.jio_key;

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getSetting('me'),
            gadget.jio_get(gadget.state.jio_key),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          page_title_translation = result[3][9];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[3][0],
                  "title": result[3][1],
                  "default": "Re: " + result[2].title,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "title",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_text_content": {
                  "description": result[3][2],
                  "title": result[3][3],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "text_content",
                  "hidden": 0,
                  "type": "TextAreaField"
                },
                "my_source": {
                  "description": "",
                  "title": result[3][4],
                  "default": result[1],
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "source",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_follow_up": {
                  "description": "",
                  "title": result[3][5],
                  "default": gadget.state.jio_key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "follow_up",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_portal_type": {
                  "description": result[3][0],
                  "title": result[3][6],
                  "default": "Web Message",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "portal_type",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_parent_relative_url": {
                  "description": "",
                  "title": result[3][8],
                  "default": "event_module",
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
                "center",
                [["my_title"], ["my_text_content"], ["my_follow_up"],
                  ["my_portal_type"], ["my_parent_relative_url"],
                  ["my_follow_up"], ["my_source"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "support_request_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'history_previous'})
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