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
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getSettingList", "getSettingList")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_get", "jio_get")
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
          return RSVP.all([form_gadget.getContent(),
                          gadget.getSettingList(['me', 'hateoas_url'])]);
        })
        .push(function (result) {
          var doc = result[0],
            me = result[1][0],
            url = result[1][1];
          return gadget.jio_putAttachment(me,
                url + me + "/Person_requestSupport",
                {title: doc.title,
                 description: doc.description,
                 aggregate: gadget.state.jio_key,
                 resource: doc.resource});
        })
        .push(function (attachment) {
          return jIO.util.readBlobAsText(attachment.target.response);
        })
        .push(function (response) {
          return JSON.parse(response.target.result);
        })
        .push(function (result) {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
            .push(function () {
              // Workaround, find a way to open document without break gadget.
              return gadget.redirect({"command": "change",
                                    "options": {"jio_key": result.relative_url, "page": "slap_controller"}});
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
          "New Ticket created.",
          "The name of a document in ERP5",
          "Subject",
          "Message",
          "Ticket Type",
          "Current User",
          "Trade Condition",
          "Aggregate",
          "Portal Type",
          "Support Request",
          "Parent Relative Url",
          "New Ticket related to"
        ];
      gadget.state.jio_key = options.jio_key;

      return new RSVP.Queue()
        .push(function () {
          return gadget.getSetting("hateoas_url");
        })
        .push(function (hateoas_url) {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_getAttachment("ticket_resource_list",
               hateoas_url + "Ticket_getResourceItemListAsJSON"),
            window.getSettingMe(gadget),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[3][0];
          page_title_translation = result[3][11];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[3][1],
                  "title": result[3][2],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_description": {
                  "description": result[3][1],
                  "title": result[3][3],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "description",
                  "hidden": 0,
                  "type": "TextAreaField"
                },
                "my_resource": {
                  "description": result[3][1],
                  "title": result[3][4],
                  "default": "",
                  "items": result[1],
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "resource",
                  "hidden": 0,
                  "type": "ListField"
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
                [["my_resource"]]
              ], [
                "center",
                [["my_title"], ["my_description"]]
              ]]
            }
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
              return gadget.jio_get(gadget.state.jio_key)
                .push(function (doc) {
                  gadget.updateHeader({
                    page_title: page_title_translation + " " + doc.title,
                    selection_url: url_list[0],
                    submit_action: true
                  });
                });
            });
        });
    });
}(window, rJS, RSVP));