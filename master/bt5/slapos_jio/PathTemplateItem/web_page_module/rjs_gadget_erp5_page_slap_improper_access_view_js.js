/*global window, rJS, RSVP, Handlebars */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    dialog_button_source = gadget_klass.__template_element
                         .getElementById("dialog-button-template")
                         .innerHTML,
    dialog_button_template = Handlebars.compile(dialog_button_source);

  gadget_klass
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("updateHeader", "updateHeader")

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
        });
    });
}(window, rJS, RSVP, Handlebars));
