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
    .declareAcquiredMethod("getSetting", "getSetting")
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
          var i, value, value_jio_key, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("portal_type")) {
              if (result.data.rows[i].value.portal_type === "Compute Node") {
                value_jio_key = result.data.rows[i].id;
                value = result.data.rows[i].value.Document_getNewsDict;
                // Use a User-friendly for the Website, this value should be translated
                // most liketly
                result.data.rows[i].value.portal_type = "Server";
                result.data.rows[i].value.Document_getNewsDict = {
                  field_gadget_param : {
                    css_class: "",
                    description: gadget.description_translation,
                    hidden: 0,
                    "default": {jio_key: value_jio_key, result: value},
                    key: "status",
                    url: "gadget_slapos_status.html",
                    title: gadget.title_translation,
                    type: "GadgetField"
                  }
                };
              }
              if (result.data.rows[i].value.portal_type === "Instance Tree") {
                value_jio_key = result.data.rows[i].id;
                value = result.data.rows[i].value.Document_getNewsDict;
                // Use a User-friendly for the Website, this value should be translated
                // most liketly
                result.data.rows[i].value.portal_type = "Service";
                result.data.rows[i].value.Document_getNewsDict = {
                  field_gadget_param : {
                    css_class: "",
                    description: gadget.description_translation,
                    hidden: 0,
                    "default": {jio_key: value_jio_key, result: value},
                    key: "status",
                    url: "gadget_slapos_status.html",
                    title: gadget.title_translation,
                    type: "GadgetField"
                  }
                };
              }
              if (result.data.rows[i].value.portal_type === "Computer Network") {
                value_jio_key = result.data.rows[i].id;
                value = result.data.rows[i].value.Document_getNewsDict;
                // Use a User-friendly for the Website, this value should be translated
                // most liketly
                result.data.rows[i].value.portal_type = "Network";
                result.data.rows[i].value.Document_getNewsDict = {
                  field_gadget_param : {
                    css_class: "",
                    description: gadget.description_translation,
                    hidden: 0,
                    "default": {jio_key: value_jio_key, result: value},
                    key: "status",
                    url: "gadget_slapos_status.html",
                    title: gadget.title_translation,
                    type: "GadgetField"
                  }
                };
              }
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
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
          "Title",
          "Reference",
          "The name of a document in ERP5",
          "Description",
          "Monitoring Status",
          "Items",
          "Project",
          "The Status",
          "Status",
          "Data updated.",
          "Type"
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
          page_title_translation = result[2][6];
          gadget.description_translation = result[2][7];
          gadget.title_translation = result[2][8];
          gadget.message_translation = result[2][9];
          var editable = gadget.state.editable,
            column_list = [
              ['title', result[2][0]],
              ['reference', result[2][1]],
              ['portal_type', result[2][10]],
              ['Document_getNewsDict', result[2][8]]
            ];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": "",
                  "title": result[2][0],
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
                  "title": result[2][1],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_description": {
                  "description": result[2][2],
                  "title": result[2][3],
                  "default": gadget.state.doc.description,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "description",
                  "hidden": 0,
                  "type": "TextAreaField"
                },
                "my_monitoring_status": {
                  "description": "",
                  "title": result[2][4],
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
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_project_compute_node2_listbox",
                  "lines": 10,
                  "list_method": "Project_getComputeNodeTrackingList",
                  "list_method_template": result[1] + "ERP5Document_getHateoas?mode=search&" +
                            "list_method=Project_getComputeNodeTrackingList&relative_url=" +
                            gadget.state.jio_key + "&default_param_json=eyJpZ25vcmVfdW5rbm93bl9jb2x1bW5zIjogdHJ1ZX0={&query,select_list*,limit*,sort_on*,local_roles*}",
                  "query": "urn:jio:allDocs?query=",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title": result[2][7],
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
                [["my_title"], ["my_reference"], ["my_description"]]
              ], [
                "right",
                [['my_monitoring_status']]
              ], [
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "project_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'}),
            gadget.getUrlFor({command: "change", options: {page: "slap_delete_project"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_project_get_invitation_link"}})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: page_title_translation + " : " + gadget.state.doc.title,
            delete_url: url_list[2],
            invitation_url: url_list[3],
            save_action: true
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));
