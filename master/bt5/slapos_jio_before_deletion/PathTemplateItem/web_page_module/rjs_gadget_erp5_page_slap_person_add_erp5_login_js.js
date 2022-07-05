/*global window, rJS, RSVP */
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
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
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
      var gadget = this,
        doc = {};
      return gadget.notifySubmitting()
        .push(function () {
          return gadget.getDeclaredGadget('form_view');
        })
        .push(function (form_gadget) {
          return RSVP.all([
            form_gadget.getContent(),
            gadget.message1_translation,
            gadget.message2_translation
          ]);
        })
        .push(function (result) {
          var k,
            content = result[0];
          for (k in content) {
            if (content.hasOwnProperty(k)) {
              if (k !== "password_confirmation") {
                doc[k] = content[k];
              }
              if ((k === "password_confirmation") &&
                  (content.password !== content.password_confirmation)) {
                return gadget.notifySubmitted({message: result[1], status: 'error'});
              }
            }
          }
          return gadget.getSetting("hateoas_url")
            .push(function (hateoas_url) {
              return gadget.jio_putAttachment(content.parent_relative_url,
                hateoas_url + gadget.state.jio_key + "/Person_newLogin", doc)
                .push(function () {
                  return gadget.notifySubmitted({message: result[2], status: 'success'});
                })
                .push(function () {
                  return gadget.redirect({"command": "change",
                    "options": {"jio_key": content.parent_relative_url,
                                "page": "slap_controller"}});
                })
                .push(undefined, function (error) {
                  return gadget.getTranslationList(["Unknown Error, please open a ticket."])
                    .push(function (error_message) {
                      if (error.target === undefined) {
                        // received a cancelation so just skip
                        return gadget;
                      }
                      return jIO.util.readBlobAsText(error.target.response)
                        .then(function (evt) {
                          if (error.target.status === 406) {
                            return gadget.notifySubmitted({message: JSON.parse(evt.target.result),
                                                           status: 'error'});
                          }
                          return gadget.notifySubmitted({message: error_message[0],
                                                      status: 'error'});
                        });
                    });
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
          "Login Name",
          "Password",
          "Confirm your Password",
          "Add New User Login",
          "The name of a document in ERP5",
          "Portal Type",
          "Parent Relative Url",
          "Password is different from confirmation",
          "New User Login created."
        ];
      gadget.state.jio_key = options.jio_key;

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message1_translation = result[1][7];
          gadget.message2_translation = result[1][8];
          page_title_translation = result[1][3];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_reference": {
                  "description": "",
                  "title": result[1][0],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_new_password": {
                  "description": "",
                  "title": result[1][1],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "password",
                  "hidden": 0,
                  "type": "PasswordField"
                },
                "my_confirmation_password": {
                  "description": "",
                  "title": result[1][2],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "password_confirmation",
                  "hidden": 0,
                  "type": "PasswordField"
                },
                "my_portal_type": {
                  "description": result[1][4],
                  "title": result[1][5],
                  "default": "ERP5 Login",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "portal_type",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_parent_relative_url": {
                  "description": "",
                  "title": result[1][6],
                  "default": gadget.state.jio_key,
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
                [["my_reference"], ["my_new_password"], ["my_confirmation_password"], ["my_portal_type"], ["my_parent_relative_url"]]
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
            gadget.getUrlFor({command: 'change', options: {page: "slap_controller"}})
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