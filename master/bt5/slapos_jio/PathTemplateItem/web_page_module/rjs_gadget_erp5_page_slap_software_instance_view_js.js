/*global window, rJS, RSVP, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, JSON) {
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
          var i, value, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("connection_key")) {
              value = result.data.rows[i].value.connection_key;
              result.data.rows[i].value.connection_key = {
                field_gadget_param : {
                  css_class: "",
                  "default": value,
                  key: "status",
                  editable: 1,
                  url: "gadget_slapos_label_listbox_field.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              value = result.data.rows[i].value.connection_value;
              result.data.rows[i].value.connection_value = {
                field_gadget_param : {
                  css_class: "",
                  "default": value,
                  key: "status",
                  editable: 1,
                  url: "gadget_slapos_label_listbox_field.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
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
        connection_key_translation,
        connection_value_translatin,
        translation_list = [
          "Title",
          "Reference",
          "Monitoring Status",
          "Software Release",
          "Instance Tree",
          "Software Type",
          "Instance Parameters",
          "Connection Parameters",
          "Parameter",
          "Value",
          "Status",
          "Data updated.",
          "Node",
          "Partition"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.getDeclaredGadget('form_view');
        })
        .push(function (form_gadget) {
          var connection_column_list = [
              ['connection_key', connection_key_translation],
              ['connection_value', connection_value_translatin]
            ];
          return new RSVP.Queue()
            .push(function () {
              return RSVP.all([
                gadget.getUrlFor({command: "change", options: {jio_key: gadget.state.doc.specialise }}),
                gadget.getSetting("hateoas_url"),
                gadget.getTranslationList(translation_list)
              ]);
            })
            .push(function (result) {
              connection_key_translation = result[2][8];
              connection_value_translatin = result[2][9];
              gadget.title_translation = result[2][10];
              gadget.message_translation = result[2][11];
              return form_gadget.render({
                erp5_document: {
                  "_embedded": {"_view": {
                    "my_title": {
                      "description": "",
                      "title": result[2][0],
                      "default": gadget.state.doc.title,
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
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
                    "my_monitoring_status": {
                      "description": "",
                      "title": result[2][2],
                      "default": "",
                      "renderjs_extra": JSON.stringify({
                        jio_key: gadget.state.jio_key,
                        result: gadget.state.doc.news
                      }),
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "url": "gadget_slapos_status.html",
                      "sandbox": "",
                      "key": "monitoring_status",
                      "hidden": gadget.state.doc.portal_type === "Slave Instance",
                      "type": "GadgetField"
                    },
                    "my_url_string": {
                      "description": "",
                      "title": result[2][3],
                      "default":
                        "<a target=_blank href=" + gadget.state.doc.url_string + ">" +
                        gadget.state.doc.url_string + "</a>",
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "key": "url_string",
                      "hidden": 0,
                      "type": "EditorField"
                    },
                    "my_specialise_title": {
                      "description": "",
                      "title": result[2][4],
                      "default":
                        "<a href=" + result[0] + ">" +
                        gadget.state.doc.specialise_title + "</a>",
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "key": "specialise_title",
                      "hidden": 0,
                      "type": "EditorField"
                    },
                    "my_source_reference": {
                      "description": "",
                      "title": result[2][5],
                      "default": gadget.state.doc.source_reference,
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "key": "source_reference",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_allocation_information": {
                      "description": "",
                      "title": result[2][12],
                      "default": gadget.state.doc.allocation_information,
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "key": "allocation_information",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_text_content": {
                      "description": "",
                      "title": result[2][6],
                      "default": gadget.state.doc.text_content,
                      "css_class": "",
                      "required": 1,
                      "editable": 0,
                      "key": "text_content",
                      "hidden": 0,
                      "type": "TextareaField"
                    },
                    "connection_listbox": {
                      "column_list": connection_column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 1,
                      "editable_column_list": [],
                      "key": "slap_connection_listbox",
                      // XXXX this listbox doesn't handle pagination correctly. Let's hope we will never have more than 100 connection parameters.
                      "lines": 100,
                      "list_method": "SoftwareInstance_getConnectionParameterList",
                      "list_method_template": result[1] + "ERP5Document_getHateoas?mode=search&" +
                        "list_method=SoftwareInstance_getConnectionParameterList&relative_url=" +
                        gadget.state.jio_key + "&default_param_json=eyJpZ25vcmVfdW5rbm93bl9jb2x1bW5zIjogdHJ1ZX0={&query,select_list*,limit*,sort_on*,local_roles*}",
                      "query": "urn:jio:allDocs?query=",
                      "portal_type": [],
                      "search_column_list": connection_column_list,
                      "sort_column_list": connection_column_list,
                      "sort": [["connection_key", "ascending"]],
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
                    [["my_title"], ["my_reference"], ['my_monitoring_status']]
                  ], [
                    "right",
                    [["my_specialise_title"], ["my_source_reference"], ["my_allocation_information"]]
                  ], [
                    "center",
                    [["my_url_string"], ["my_text_content"]]
                  ], [
                    "bottom",
                    [["connection_listbox"]]
                  ]]
                }
              });
            });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "software_instance_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: gadget.state.doc.portal_type +
              " : " + gadget.state.doc.title
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, JSON));