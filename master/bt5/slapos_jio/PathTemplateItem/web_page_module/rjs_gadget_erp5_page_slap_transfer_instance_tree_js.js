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
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
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
              return gadget.jio_putAttachment(doc.relative_url,
                url + doc.relative_url + "/InstanceTree_createMovement", doc);
            })
            .push(function () {
              return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
                .push(function () {
                  // Workaround, find a way to open document without break gadget.
                  return gadget.redirect({"command": "change",
                                      "options": {"jio_key": doc.relative_url, "page": "slap_controller"}});
                });
            });
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        translation_list = [
          "The name of a document in ERP5",
          "Title",
          "Reference",
          "Project",
          "Organisation",
          "Parent Relative Url",
          "Transfer Service",
          "Service will be transferred soon."
        ];
      return new RSVP.Queue()
        .push(function () {
          return window.getSettingMe(gadget);
        })
        .push(function (me) {
          return gadget.jio_get(me);
        })
        .push(function (me) {
          var i, destination_list = '"NULL",';
          for (i in me.assignment_destination_list) {
            if (me.assignment_destination_list.hasOwnProperty(i)) {
              destination_list += '"' + me.assignment_destination_list[i] + '",';
            }
          }
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_get(options.jio_key),
            gadget.jio_allDocs({
              query: 'portal_type:"Organisation" AND role_title: "Client" AND relative_url:(' + destination_list + ')',
              sort_on: [['title', 'descending']],
              select_list: ['reference', 'title'],
              limit: 1000
            }),
            gadget.jio_allDocs({
              query: 'portal_type:"Project" AND validation_state:"validated"',
              sort_on: [['title', 'descending']],
              select_list: ['reference', 'title'],
              limit: 1000
            }),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[4][7];
          gadget.page_title_translation = result[4][6];
          var doc = result[1],
            default_organisation = "",
            default_project = "",
            organisation_list = [["", ""]],
            project_list = [["", ""]],
            i,
            project_len = result[3].data.total_rows,
            site_len = result[2].data.total_rows;

          for (i = 0; i < site_len; i += 1) {
            if (result[2].data.rows[i].value.title === doc.source_title) {
              default_organisation = result[2].data.rows[i].id;
            }
            organisation_list.push([
              result[2].data.rows[i].value.title || result[2].data.rows[i].value.reference,
              result[2].data.rows[i].id
            ]);
          }

          for (i = 0; i < project_len; i += 1) {
            if (result[3].data.rows[i].value.title === doc.source_project_title) {
              default_project = result[3].data.rows[i].id;
            }
            project_list.push([
              result[3].data.rows[i].value.title || result[3].data.rows[i].value.reference,
              result[3].data.rows[i].id
            ]);
          }

          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[4][0],
                  "title": result[4][1],
                  "default": doc.title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": result[4][0],
                  "title": result[4][2],
                  "default": doc.reference,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_destination": {
                  "description": result[4][0],
                  "title": result[4][4],
                  "default": default_organisation,
                  "items": organisation_list,
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "key": "destination",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_destination_project": {
                  "description": result[4][0],
                  "title": result[4][3],
                  "default": default_project,
                  "items": project_list,
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "key": "destination_project",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_relative_url": {
                  "description": "",
                  "title": result[4][5],
                  "default": options.jio_key,
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "key": "relative_url",
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
                [["my_title"], ["my_reference"], ["my_destination_project"],
                  ["my_destination"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "instance_tree_module"
          });
        })
        .push(function () {
          return gadget.getUrlFor({command: 'history_previous'});
        })
        .push(function (selection_url) {
          return gadget.updateHeader({
            selection_url: selection_url,
            page_title: gadget.page_title_translation,
            submit_action: true
          });
        });
    });
}(window, rJS, RSVP));