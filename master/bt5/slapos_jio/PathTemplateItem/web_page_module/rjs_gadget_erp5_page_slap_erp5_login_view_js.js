/*global window, rJS, RSVP, jIO, Blob, UriTemplate */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, jIO, UriTemplate) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getUrlParameter", "getUrlParameter")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")
    .declareAcquiredMethod("redirect", "redirect")



    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////


    .declareMethod("render", function (options) {
      return this.changeState({
        jio_key: options.jio_key,
        doc: options.doc,
        editable: 1
      });
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
            if (content.hasOwnProperty(k)) {
              if (k !== "password_confirmation") {
                doc[k] = content[k];
              }
              if ((k === "password_confirmation") &&
                  (content.password !== content.password_confirmation)) {
                return gadget.notifySubmitted({message: gadget.message1_translation, status: 'error'});
              }
            }
          }
          return gadget.jio_getAttachment('acl_users', 'links')
            .push(function (links) {
              var logout_url_template = links._links.logout.href;
              return gadget.getSetting("hateoas_url")
                .push(function (hateoas_url) {
                  return gadget.jio_putAttachment(gadget.state.jio_key,
                      hateoas_url + gadget.state.jio_key + "/Login_edit", doc);
                })
                .push(function (response) {
                  if (response.target === undefined) {
                    return gadget.notifySubmitted({message: gadget.message2_translation, status: 'success'});
                  }
                  // This is probably not ok
                  if (response.target.status === 200 && response.target.responseURL.search("login_form")) {
                    // The script required to launch a redirect
                    return gadget.notifySubmitted({message: gadget.message2_translation, status: 'success'})
                      .push(function () {
                        return gadget.getSetting('frontpage_gadget');
                      })
                      .push(function (frontpage_gadget) {
                        return gadget.getUrlFor({
                          command: 'display',
                          absolute_url: true,
                          options: {"jio_key": "/", "page": frontpage_gadget}
                        })
                      })
                      .push(function (came_from) {
                        return gadget.redirect({
                          command: 'raw',
                          options: {
                            url: UriTemplate.parse(logout_url_template).expand({came_from: came_from})
                          }
                        });
                      });
                  }
                  return gadget.notifySubmitted({message: gadget.message2_translation, status: 'success'});
                });
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
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .onStateChange(function () {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Password is different from confirmation",
          "Data updated.",
          "Reference",
          "Password",
          "Confirm your Password",
          "Login"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getSetting("hateoas_url"),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message1_translation = result[2][0];
          gadget.message2_translation = result[2][1];
          page_title_translation = result[2][5];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_reference": {
                  "description": "",
                  "title": result[2][2],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_new_password": {
                  "description": "",
                  "title": result[2][3],
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
                  "title": result[2][4],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "password_confirmation",
                  "hidden": 0,
                  "type": "PasswordField"
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
                [["my_reference"], ["my_new_password"], ["my_confirmation_password"] ]
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
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'}),
            gadget.getUrlFor({command: "change", options: {page: "slap_invalidate_login"}})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: page_title_translation + " : " + gadget.state.doc.reference,
            delete_url: url_list[2],
            save_action: true
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, jIO, UriTemplate));