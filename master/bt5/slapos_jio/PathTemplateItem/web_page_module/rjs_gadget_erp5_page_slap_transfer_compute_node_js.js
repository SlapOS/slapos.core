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
    .declareAcquiredMethod("translate", "translate")
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
              // This is horrible
              return gadget.jio_putAttachment(doc.relative_url,
                url + doc.relative_url + "/ComputeNode_createMovement", doc);
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
        page_translation,
        translation_list = [
          "Compute Node is transferred.",
          "The name of a document in ERP5",
          "Title",
          "Reference",
          "Current Location",
          "Current Project",
          "Future Location",
          "Future Project",
          "Current Organisation",
          "Future Organisation",
          "Parent Relative Url",
          "Transfer Compute Node"
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
              query: 'portal_type:"Organisation" AND role_title: "Host" AND relative_url:(' + destination_list + ')',
              sort_on: [['reference', 'ascending']],
              select_list: ['reference', 'title']
            }),
            gadget.jio_allDocs({
              query: 'portal_type:"Project" AND validation_state:"validated"',
              sort_on: [['reference', 'ascending']],
              select_list: ['reference', 'title']
            }),
            gadget.jio_allDocs({
              query: 'portal_type:"Organisation" AND role_title: "Client" AND relative_url:(' + destination_list + ')',
              sort_on: [['reference', 'ascending']],
              select_list: ['reference', 'title']
            }),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[5][0];
          page_translation = result[5][11];
          var doc = result[1],
            site_list = [["", ""]],
            project_list = [["", ""]],
            organisation_list = [["", ""]],
            i,
            project_len = result[3].data.total_rows,
            site_len = result[2].data.total_rows,
            organisation_len = result[4].data.total_rows;

          for (i = 0; i < site_len; i += 1) {
            site_list.push([
              result[2].data.rows[i].value.title || result[2].data.rows[i].value.reference,
              result[2].data.rows[i].id
            ]);
          }

          for (i = 0; i < project_len; i += 1) {
            project_list.push([
              result[3].data.rows[i].value.title || result[3].data.rows[i].value.reference,
              result[3].data.rows[i].id
            ]);
          }

          for (i = 0; i < organisation_len; i += 1) {
            organisation_list.push([
              result[4].data.rows[i].value.title || result[4].data.rows[i].value.reference,
              result[4].data.rows[i].id
            ]);
          }

          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": result[5][1],
                  "title": result[5][2],
                  "default": doc.title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": result[5][1],
                  "title": result[5][3],
                  "default": doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_source": {
                  "description": result[5][1],
                  "title": result[5][4],
                  "default": doc.source_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "source_title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_source_project": {
                  "description": result[5][1],
                  "title": result[5][5],
                  "default": doc.source_project_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "source_project_title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_destination": {
                  "description": result[5][1],
                  "title": result[5][6],
                  "default": "",
                  "items": site_list,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "destination",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_destination_project": {
                  "description": result[5][1],
                  "title": result[5][7],
                  "default": "",
                  "items": project_list,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "destination_project",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_source_section": {
                  "description": result[5][1],
                  "title": result[5][8],
                  "default": doc.source_section_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "source_section_title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_destination_section": {
                  "description": result[5][1],
                  "title": result[5][9],
                  "default": "",
                  "items": organisation_list,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "destination_section",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_relative_url": {
                  "description": "",
                  "title": result[5][10],
                  "default": options.jio_key,
                  "css_class": "",
                  "required": 1,
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
                [["my_title"], ["my_reference"], ["my_source_section"], ["my_source"], ["my_source_project"],
                  ["my_destination"], ["my_destination_project"], ["my_destination_section"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "compute_node_module"
          });
        })
        .push(function () {
          return gadget.getUrlFor({command: 'history_previous'});
        })
        .push(function (selection_url) {
          return gadget.updateHeader({
            selection_url: selection_url,
            page_title: page_translation,
            submit_action: true
          });
        });
    });
}(window, rJS, RSVP));