/*global window, rJS, RSVP, jIO, Blob */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getUrlParameter", "getUrlParameter")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (1 || (result.data.rows[i].value.hasOwnProperty("ComputeNode_getNewsDict"))) {
              value = result.data.rows[i].value.ComputeNode_getNewsDict;
              result.data.rows[i].value.ComputeNode_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  "default": {jio_key: value, result: value, portal_type: "Compute Node"},
                  key: "status",
                  url: "gadget_slapos_status.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                //key: "listbox_uid:list",
                //value: 2713
              };
            }
          }
          return result;
        });
    })

    .declareMethod("render", function (options) {
      return this.changeState({
        jio_key: options.jio_key,
        doc: options.doc,
        editable: 1
      });
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
        .push(function (content) {
          return gadget.updateDocument(content);
        })
        .push(function () {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .onStateChange(function () {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Data updated.",
          "Title",
          "Reference",
          "Allocation Scope",
          "Status",
          "Monitoring Status",
          "The name of a document in ERP5",
          "Current Project",
          "Current Organisation",
          "Associated Servers",
          "Computer Network"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.title_translation = result[1][4];
          gadget.message_translation = result[1][0];
          page_title_translation = result[1][10];
          var editable = gadget.state.editable,
            column_list = [
              ['title', result[1][1]],
              ['reference', result[1][2]],
              ['allocation_scope_translated_title', result[1][3]],
              ['ComputeNode_getNewsDict', result[1][4]]
            ];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": "",
                  "title": result[1][1],
                  "default": gadget.state.doc.title,
                  "css_class": "",
                  "required": 1,
                  "editable": editable,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": "",
                  "title": result[1][2],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_monitoring_status": {
                  "description": "",
                  "title": result[1][5],
                  "default": {jio_key: gadget.state.jio_key,
                              result: gadget.state.doc.news},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_status.html",
                  "sandbox": "",
                  "key": "monitoring_status",
                  "hidden": 0,
                  "type": "GadgetField"
                },
                "my_source_project": {
                  "description": result[1][6],
                  "title": result[1][7],
                  "default": gadget.state.doc.source_project_title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_source_section": {
                  "description": result[1][6],
                  "title": result[1][8],
                  "default": gadget.state.doc.source_section_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "",
                  "hidden": 0,
                  "type": "StringField"
                },
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_project_compute_node_listbox",
                  "lines": 10,
                  "list_method": "portal_catalog",
                  // XXX TODO Filter by   default_strict_allocation_scope_uid="!=%s" % context.getPortalObject().portal_categories.allocation_scope.close.forever.getUid(),
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Compute Node" + "%22%20AND%20" +
                    "subordination_reference%3A" + gadget.state.doc.reference,
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
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
                [["my_title"], ["my_reference"]]
              ], [
                "right",
                [['my_monitoring_status'], ["my_source_project"], ["my_source_section"]]
              ], [
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "computer_network_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'}),
            gadget.getUrlFor({command: "change", options: {page: "slap_delete_network"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_transfer_computer_network"}})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: page_title_translation + " :" + gadget.state.doc.title,
            delete_url: url_list[2],
            transfer_url: url_list[3],
            save_action: true
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));