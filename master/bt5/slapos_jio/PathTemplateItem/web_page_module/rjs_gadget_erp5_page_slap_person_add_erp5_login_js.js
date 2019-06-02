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
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')

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
          return form_gadget.getContent();
        })
        .push(function (content) {
          var k;
          for (k in content) {
            if (k !== "password_confirmation") {
              doc[k] = content[k];
            }
            if ((k === "password_confirmation") &&
                (content.password !== content.password_confirmation)) {
              return gadget.notifySubmitted({message: 'Password is different from confirmation', status: 'error'});
            }
          }
          return gadget.getSetting("hateoas_url")
            .push(function (hateoas_url) {
              return gadget.jio_putAttachment(content.parent_relative_url,
                hateoas_url + gadget.state.jio_key + "/Person_newLogin", doc)
                .push(function () {
                  return gadget.notifySubmitted({message: 'New User Login created.', status: 'success'});
                })
                .push(function () {
                  return gadget.redirect({"command": "change",
                    "options": {"jio_key": content.parent_relative_url,
                                "page": "slap_controller"}});
                });
            });
        });
    })
    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })
    .declareMethod("render", function (options) {
      var gadget = this;
      gadget.state.jio_key = options.jio_key;

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view')
          ]);
        })
        .push(function (result) {
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_reference": {
                  "description": "",
                  "title": "Login Name",
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
                  "title": "Password",
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
                  "title": "Confirm your Password",
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "password_confirmation",
                  "hidden": 0,
                  "type": "PasswordField"
                },
                "my_portal_type": {
                  "description": "The name of a document in ERP5",
                  "title": "Portal Type",
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
                  "title": "Parent Relative Url",
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
          return RSVP.all([
            gadget.getUrlFor({command: 'change', options: {page: "slap_controller"}})
          ]);
        })
        .push(function (url_list) {
          return gadget.updateHeader({
            page_title: "Add New User Login",
            selection_url: url_list[0],
            submit_action: true
          });
        });
    });
}(window, rJS, RSVP));