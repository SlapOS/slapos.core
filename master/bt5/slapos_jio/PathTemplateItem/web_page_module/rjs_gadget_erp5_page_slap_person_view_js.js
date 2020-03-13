/*global window, rJS, RSVP, jIO, Blob */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getUrlParameter", "getUrlParameter")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_put", "jio_put")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////


    .declareMethod('updateDocument', function (content) {
      var gadget = this, property, doc = {};
      for (property in content) {
        if ((content.hasOwnProperty(property)) &&
            // Remove undefined keys added by Gadget fields
            (property !== "undefined") &&
            // Remove listboxes UIs
            (property !== "listbox_uid:list") &&
            // Remove default_*:int keys added by ListField
            !(property.endsWith(":int") && property.startsWith("default_"))) {
          doc[property] = content[property];
        }
      }
      return gadget.jio_put(gadget.state.jio_key, doc);
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        jio_key;

      return new RSVP.Queue()
        .push(function () {
          return window.getSettingMe(gadget);
        })
        .push(function (me) {
          jio_key = me;
          return gadget.jio_get(me);
        })
        .push(function (doc) {
          options.doc = doc;
          return gadget.changeState({
            jio_key: jio_key,
            doc: doc,
            editable: 1
          });
        });
    })

    .onEvent('submit', function () {
      var gadget = this;
      return gadget.notifySubmitting()
        .push(function () {
          return gadget.getDeclaredGadget('form_view');
        })
        .push(function (form_gadget) {
          return RSVP.all([
            form_gadget.getContent(),
            gadget.account_translation
          ]);
        })
        .push(function (result) {
          var content = result[0];
          return gadget.updateDocument(content)
            .push(function () {
              return gadget.updateHeader({
                page_title: result[1] + " : " + content.first_name + " " + content.last_name
              });
            });
        })
        .push(function () {
          return gadget.message_translation;
        })
        .push(function (result) {
          return gadget.notifySubmitted({message: result, status: 'success'});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .onStateChange(function () {
      var gadget = this,
        translation_list = [
          "Reference",
          "Type",
          "Title",
          "Region",
          "Status",
          "First Name",
          "Last Name",
          "Email",
          "Logins",
          "Organisations",
          "Your Account",
          "Data updated"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.account_translation = result[1][10];
          gadget.message_translation = result[1][11];
          var form_gadget = result[0],
            i,
            destination_list,
            column_list = [
              ['reference', result[1][0]],
              ['portal_type', result[1][1]]
            ],
            organisation_column_list = [
              ['title', result[1][2]],
              ['reference', result[1][0]],
              ['default_address_region_title', result[1][3]],
              ['Organisation_getNewsDict', result[1][4]]
            ];
          destination_list = "%22NULL%22%2C";
          for (i in gadget.state.doc.assignment_destination_list) {
            if (gadget.state.doc.assignment_destination_list.hasOwnProperty(i)) {
              destination_list += "%22" + gadget.state.doc.assignment_destination_list[i] + "%22%2C";
            }
          }
          return form_gadget.render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_first_name": {
                  "description": "",
                  "title": result[1][5],
                  "default": gadget.state.doc.first_name,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "first_name",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_last_name": {
                  "description": "",
                  "title": result[1][6],
                  "default": gadget.state.doc.last_name,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "last_name",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_default_email_text": {
                  "description": "",
                  "title": result[1][7],
                  "default": gadget.state.doc.default_email_text,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "default_email_text",
                  "hidden": 0,
                  "type": "StringField"
                },
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_person_login_listbox",
                  "lines": 20,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=%28portal_type%3A%28%22" +
                    "ERP5 Login" + "%22%2C%20%22" +
                    "Google Login" + "%22%2C%20%22" +
                    "Facebook Login" + "%22%29%20AND%20" +
                    "validation_state%3Avalidated%29",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["reference", "ascending"]],
                  "title": result[1][8],
                  "type": "ListBox"
                },
                "organisation_listbox": {
                  "column_list": organisation_column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_person_organisation_listbox",
                  "lines": 20,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Organisation" + "%22%20AND%20role_title%3A%22Client%22%20AND%20" +
                    "relative_url%3A(" + destination_list + ")",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["reference", "ascending"]],
                  "title": result[1][9],
                  "type": "ListBox"
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
                [["my_first_name"], ["my_last_name"], ["my_default_email_text"]]
              ], [
                "bottom",
                [["listbox"], ["organisation_listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return window.getSettingMe(gadget);
        })
        .push(function (me) {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: "change", options: {jio_key: me, page: "slap_person_revoke_certificate"}}),
            gadget.getUrlFor({command: "change", options: {jio_key: me, page: "slap_person_request_certificate"}}),
            gadget.getUrlFor({command: "change", options: {jio_key: me, page: "slap_person_get_token"}}),
            gadget.getUrlFor({command: "change", options: {jio_key: me, page: "slap_person_add_erp5_login"}}),
            gadget.getUrlFor({command: "change", options: {jio_key: me, page: "slap_person_add_organisation"}}),
            gadget.getUrlFor({command: "change", options: {page: "slapos"}})
          ]);
        })
        .push(function (result) {
          var header_dict = {
            page_title: gadget.account_translation + " : " + gadget.state.doc.first_name + " " + gadget.state.doc.last_name,
            save_action: true,
            request_certificate_url: result[2],
            revoke_certificate_url: result[1],
            token_url: result[3],
            add_login_url: result[4],
            add_organisation_url: result[5],
            selection_url: result[6]
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = result[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));