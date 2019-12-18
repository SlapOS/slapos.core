/*global window, rJS, RSVP, Handlebars, UriTemplate */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, Handlebars, UriTemplate) {
  "use strict";
  var gadget_klass = rJS(window),
    dialog_button_source = gadget_klass.__template_element
                         .getElementById("dialog-button-template")
                         .innerHTML,
    dialog_button_template = Handlebars.compile(dialog_button_source);

  gadget_klass
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translate", "translate")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod("render", function () {
      var gadget = this;

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getUrlForList([{command: 'display'}]),
            gadget.getDeclaredGadget("erp5_form")
          ]);
        })
        .push(function (result_list) {
          var user,
            key,
            list_item = [];

          return RSVP.all([
            gadget.updateHeader({
              page_title: 'Error page',
              front_url: result_list[0][0]
            }),

            result_list[1].render({
              erp5_document: {"_embedded": {"_view": {
                'Message': {
                  "default": "You are not allowed to access this content, please login with an user which has the right permission",
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
          return gadget.translate('Logout');
        })
        .push(function (translated_text) {
          gadget.element.querySelector('input').value = translated_text;
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
}(window, rJS, RSVP, Handlebars, UriTemplate));
