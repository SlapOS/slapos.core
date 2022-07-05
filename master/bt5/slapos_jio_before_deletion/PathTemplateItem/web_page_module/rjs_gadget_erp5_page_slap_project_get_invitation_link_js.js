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
              return gadget.jio_getAttachment(doc.relative_url,
                url + doc.relative_url + "/Base_getInvitationLink");
            })
            .push(function (result) {
              return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
                .push(function () {
                  // Workaround, find a way to open document without break gadget.
                  result.jio_key = doc.relative_url;
                  return gadget.render(result);
                });
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
          "New Invitation link generated.",
          "Parent Relative Url",
          "Your Invitation Link",
          "Generate New Invitation Link"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[1][0];
          page_title_translation = result[1][3];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_relative_url": {
                  "description": "",
                  "title": result[1][1],
                  "default": options.jio_key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "relative_url",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_invitation_link": {
                  "description": "",
                  "title": result[1][2],
                  "default": options.invitation_link,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "invitation_link",
                  "hidden": (options.invitation_link === undefined) ? 1 : 0,
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
                [["my_invitation_link"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "project_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'history_previous'})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            page_title: page_title_translation,
            submit_action: true,
            selection_url: url_list[0]
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));