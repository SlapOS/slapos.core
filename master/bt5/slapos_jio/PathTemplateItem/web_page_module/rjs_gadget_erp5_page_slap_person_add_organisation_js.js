/*global window, rJS, RSVP, jIO*/
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, jIO) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getSettingList", "getSettingList")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
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
                url + me + "/Person_requestOrganisation", {title: doc.title});
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

    .declareMethod("render", function () {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Title",
          "New Organisation",
          "The name of a document in ERP5",
          "Role Definition",
          "Role",
          "Portal Type",
          "Parent Relative Url",
          "New Organisation created."
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[1][7];
          page_title_translation = result[1][1];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[1][2],
                  "title": result[1][0],
                  "default": "",
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "key": "title",
                  "hidden": 0,
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
                [["my_title"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "person_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'change', options: {page: "slap_person_view"}})
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
}(window, rJS, RSVP, jIO));