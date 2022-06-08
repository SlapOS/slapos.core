/*global window, rJS, RSVP, UriTemplate */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, UriTemplate) {
  "use strict";
  rJS(window)
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod("render", function () {
      var gadget = this,
        logout_translation,
        translation_list = [
          "You are not allowed to access this content, please login with an user which has the right permission",
          "Error page",
          "Logout"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getUrlForList([{command: 'display'}]),
            gadget.getDeclaredGadget("erp5_form"),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result_list) {
          logout_translation = result_list[2][2];
          return RSVP.all([
            gadget.updateHeader({
              page_title: result_list[2][1],
              front_url: result_list[0][0]
            }),

            result_list[1].render({
              erp5_document: {"_embedded": {"_view": {
                'Message': {
                  "default": result_list[2][0],
                  "editable": 0,
                  "key": "field_message",
                  "title": "",
                  "type": "StringField"
                }
              }},
                "_links": {
                  "type": {
                    name: ""
                  }
                }
                },
              form_definition: {
                group_list: [[
                  "left",
                  [["Message"]]
                ]]
              }
            })
          ]);
        })
        .push(function () {
          gadget.element.querySelector('input').value = logout_translation;
          return gadget.updatePanel({
            jio_key: false
          });
        });
    })
      .onEvent('submit', function () {
      var gadget = this,
        logout_url_template;

      return gadget.jio_getAttachment('acl_users', 'links')
        .push(function (links) {
          logout_url_template = links._links.logout.href;
          return gadget.getUrlFor({
            command: 'display',
            absolute_url: true,
            options: {}
          });
        })
        .push(function (came_from) {
          return gadget.redirect({
            command: 'raw',
            options: {
              url: UriTemplate.parse(logout_url_template).expand({came_from: came_from})
            }
          });
        });
    })
    .declareMethod("triggerSubmit", function () {
      return;
    });
}(window, rJS, RSVP, UriTemplate));
