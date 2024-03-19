/*global window, rJS, RSVP, jIO, btoa, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, jIO, btoa, JSON) {
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
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_allDocs", 'jio_allDocs')
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
            if (1 || (result.data.rows[i].value.SoftwareInstance_getNewsDict)) {
              value = result.data.rows[i].value.SoftwareInstance_getNewsDict;
              value_jio_key = result.data.rows[i].id;
              result.data.rows[i].value.SoftwareInstance_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: gadget.description_translation,
                  hidden:  0,
                  "default": "",
                  renderjs_extra: JSON.stringify({
                    jio_key: value_jio_key,
                    result: value
                  }),
                  key: "status",
                  url: "gadget_slapos_status.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
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

    .declareMethod('updateDocument', function (param_list) {
      var gadget = this, property,
        content = param_list, doc = {};
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
      return gadget.getSetting("hateoas_url")
        .push(function (hateoas_url) {
          return gadget.jio_putAttachment(gadget.state.jio_key,
            hateoas_url + gadget.state.jio_key + "/InstanceTree_edit", doc);
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
          "The Status",
          "Status",
          "Data updated.",
          "Title",
          "Reference",
          "Type",
          "Enabled",
          "Disabled",
          "Auto Upgrade",
          "Ask Confirmation before Upgrade",
          "Never Upgrade",
          "State",
          "Modification Date",
          "Parameter",
          "Value",
          "Short Title",
          "Description",
          "Software Type",
          "Software Release",
          "Configuration Parameter",
          "The name of a document in ERP5",
          "Current Project",
          "Current Organisation",
          "Monitoring Status",
          "Monitoring",
          "Upgrade",
          "Connection Parameters",
          "Associated Tickets",
          "Instances",
          "Instance Tree:",
          "Software Logo",
          "Node"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.getSetting("hateoas_url");
        })
        .push(function (hateoas_url) {
          return gadget.jio_getAttachment(gadget.state.jio_key,
            hateoas_url + gadget.state.jio_key +
            '/InstanceTree_getDefaultImageAbsoluteUrl',
            {});
        })
        .push(function (blob) {
          return jIO.util.readBlobAsText(blob);
        })
        .push(function (result) {
          gadget.state.doc.list_image = result.srcElement.result;
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.description_translation = result[1][0];
          gadget.title_translation = result[1][1];
          gadget.message_translation = result[1][2];
          page_title_translation = result[1][29];
          var form_gadget = result[0],
            column_list = [
              ['title', result[1][3]],
              ['reference', result[1][4]],
              ['portal_type', result[1][5]],
              ['SoftwareInstance_getAllocationInformation', result[1][31]],
              ['SoftwareInstance_getReportedState', result[1][11]],
              ['SoftwareInstance_getNewsDict', result[1][1]]
            ],
            monitor_scope_list = [['', ''],
                                [result[1][6], 'enabled'],
                                [result[1][7], 'disabled']
              ],
            upgrade_scope_list = [['', ''],
                                [result[1][8], 'auto'],
                                [result[1][9], 'ask_confirmation'],
                                [result[1][10], 'never']
              ],
            ticket_column_list = [
              ['title', result[1][1]],
              ['reference', result[1][4]],
              ['modification_date', result[1][12]],
              ['translated_simulation_state_title', result[1][11]]
            ],
            connection_column_list = [
              ['connection_key', result[1][13]],
              ['connection_value', result[1][14]]
            ],
            parameter_dict = {
              'json_url': gadget.state.doc.url_string.split('?')[0] + ".json",
              'softwaretype': gadget.state.doc.source_reference,
              'shared': gadget.state.doc.root_slave ? 1 : 0,
              'parameter_xml': '<?xml version="1.0" encoding="utf-8" ?><instance></instance>'
            };
          if (gadget.state.doc.text_content !== undefined) {
            parameter_dict.parameter_xml = gadget.state.doc.text_content;
          }
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              return form_gadget.render({
                erp5_document: {
                  "_embedded": {"_view": {
                    "my_title": {
                      "description": "",
                      "title": result[1][3],
                      "default": gadget.state.doc.title,
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "title",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_short_title": {
                      "description": "",
                      "title": result[1][15],
                      "default": gadget.state.doc.short_title,
                      "css_class": "",
                      "required": 0,
                      "editable": 1,
                      "key": "short_title",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_description": {
                      "description": "",
                      "title": result[1][16],
                      "default": gadget.state.doc.description,
                      "css_class": "",
                      "required": 0,
                      "editable": 1,
                      "key": "description",
                      "hidden": 0,
                      "type": "TextAreaField"
                    },
                    "my_reference": {
                      "description": "",
                      "title": result[1][4],
                      "default": gadget.state.doc.reference,
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "reference",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_slap_state_title": {
                      "description": "",
                      "title": result[1][11],
                      "default": gadget.state.doc.slap_state_title,
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "slap_state_title",
                      "hidden": 0,
                      "type": "StringField"
                    },
                    "my_url_string": {
                      "description": "",
                      "title": result[1][18],
                      "default":
                        "<a target=_blank href=" + gadget.state.doc.url_string + ">" +
                        gadget.state.doc.url_string + "</a>",
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "url_string",
                      "hidden": 0,
                      "type": "EditorField"
                    },
                    "my_text_content": {
                      "description": "",
                      "title": result[1][19],
                      "default": "",
                      "css_class": "",
                      "required": 0,
                      "editable": 1,
                      "url": "gadget_erp5_page_slap_parameter_form.html",
                      "sandbox": "",
                      "key": "text_content",
                      "hidden": 0,
                      "type": "GadgetField",
                      "renderjs_extra": JSON.stringify(parameter_dict)

                    },
                    "my_source_project": {
                      "description": result[1][20],
                      "title": result[1][21],
                      "default": gadget.state.doc.source_project_title,
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "source_project_title",
                      "hidden": gadget.state.doc.source_project_title ? 0 : 1,
                      "type": "StringField"
                    },
                    "my_source": {
                      "description": result[1][20],
                      "title": result[1][22],
                      "default": gadget.state.doc.source_title,
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "key": "source_title",
                      "hidden": gadget.state.doc.source_title ? 0 : 1,
                      "type": "StringField"
                    },
                    "my_monitoring_status": {
                      "description": "",
                      "title": result[1][23],
                      "default": "",
                      "renderjs_extra": JSON.stringify({
                        jio_key: gadget.state.jio_key,
                        result: gadget.state.doc.news
                      }),
                      "css_class": "",
                      "required": 0,
                      "editable": 0,
                      "url": "gadget_slapos_status.html",
                      "sandbox": "",
                      "key": "monitoring_status",
                      "hidden": 0,
                      "type": "GadgetField"
                    },
                    "my_monitor_scope": {
                      "description": "",
                      "title": result[1][24],
                      "default": gadget.state.doc.monitor_scope,
                      "css_class": "",
                      "items": monitor_scope_list,
                      "required": 0,
                      "editable": 1,
                      "key": "monitor_scope",
                      "hidden": gadget.state.doc.root_slave ? 1 : 0,
                      "type": "ListField"
                    },
                    "my_upgrade_scope": {
                      "description": "",
                      "title": result[1][25],
                      "default": gadget.state.doc.upgrade_scope,
                      "css_class": "",
                      "items": upgrade_scope_list,
                      "required": 0,
                      "editable": 1,
                      "key": "upgrade_scope",
                      "hidden": gadget.state.doc.root_slave ? 1 : 0,
                      "type": "ListField"
                    },
                    "connection_listbox": {
                      "column_list": connection_column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 1,
                      "editable_column_list": [],
                      "key": "slap_connection_listbox",
                      "lines": 30,
                      "list_method": "InstanceTree_getConnectionParameterList",
                      "list_method_template": url + "ERP5Document_getHateoas?mode=search&" +
                            "list_method=InstanceTree_getConnectionParameterList&relative_url=" +
                            gadget.state.jio_key + "&default_param_json=eyJpZ25vcmVfdW5rbm93bl9jb2x1bW5zIjogdHJ1ZX0={&query,select_list*,limit*,sort_on*,local_roles*}",
                      "query": "urn:jio:allDocs?query=",
                      "portal_type": [],
                      "search_column_list": connection_column_list,
                      "sort_column_list": connection_column_list,
                      "sort": [["connection_key", "ascending"]],
                      "title": result[1][26],
                      "type": "ListBox"
                    },
                    "ticket_listbox": {
                      "column_list": ticket_column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 1,
                      "editable_column_list": [],
                      "key": "slap_ticket_listbox",
                      "lines": 10,
                      relative_url: gadget.state.jio_key,
                      "list_method": "portal_catalog",
                      "query": "urn:jio:allDocs?query=portal_type%3A%20%28%20%22" +
                        "Support Request" + "%22%2C%20%22" +
                        "Upgrade Decision" + "%22%29%20AND%20" +
                        "default_or_child_aggregate_reference" +
                        "%3A%22" + gadget.state.doc.reference + "%22%20AND%20" +
                        "simulation_state" + "%3A%28%22" +
                        "validated" + "%22%2C%22" + "suspended" +
                        "%22%2C%22" + "confirmed" + "%22%2C%22" +
                        "started" + "%22%2C%22" + "stopped" + "%22%29",
                      "portal_type": [],
                      "search_column_list": ticket_column_list,
                      "sort_column_list": ticket_column_list,
                      "sort": [["modification_date", "descending"]],
                      "title": result[1][27],
                      "type": "ListBox"
                    },
                    "listbox": {
                      "column_list": column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 1,
                      "editable_column_list": [],
                      "key": "slap_project_compute_node_listbox",
                      "lines": 20,
                      "list_method": "portal_catalog",
                      "query": "urn:jio:allDocs?query=%28portal_type%3A%28%22" +
                        "Slave Instance" + "%22%2C%20%22" +
                        "Software Instance" + "%22%29%20AND%20%28" +
                        "default_specialise_reference%3A%22" +
                        gadget.state.doc.reference + "%22%29%20AND%20%28" +
                        "validation_state%3A%22validated%22%29%29",
                      "portal_type": [],
                      "search_column_list": column_list,
                      "sort_column_list": column_list,
                      "sort": [["title", "ascending"]],
                      "title": result[1][28],
                      "type": "ListBox"
                    },
                    "my_list_image": {
                      "css_class": "",
                      "default": gadget.state.doc.list_image +
                        "?quality=75.0&amp;display=thumbnail&amp;format=png",
                      "description": "",
                      "editable": 1,
                      "hidden": 0,
                      "key": "list_image",
                      "required": 0,
                      "title": result[1][30],
                      "type": "ImageField"
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
                    [["my_title"], ["my_reference"], ["my_short_title"], ["my_description"]]
                  ], [
                    "right",
                    [["my_slap_state_title"],  ['my_monitoring_status'], ['my_monitor_scope'], ['my_upgrade_scope'], ['my_source_project'], ['my_source']]

                  ], ["center",
                      [["my_url_string"], ["my_list_image"]]
                    ], [
                    "bottom",
                    [["ticket_listbox"], ["connection_listbox"], ["my_text_content"], ["listbox"]]
                  ]]
                }
              });
            });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "instance_tree_module"
          });
        })
        .push(function () {
          var fast_input_dict = {
            command: "display",
            options: {
              page: "slap_intent",
              intent: "request",
              shared: 1,
              software_type: gadget.state.doc.source_reference,
              software_release:  gadget.state.doc.url_string,
              sla_xml: gadget.state.doc.fast_input_dict.sla_xml,
              strict: "True"
            }
          };
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_related_ticket"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_start_instance_tree"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_stop_instance_tree"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_destroy_instance_tree"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_rss_ticket"}}),
            gadget.getUrlFor({command: 'history_previous'}),
            gadget.getUrlFor({command: "change", options: {page: "slap_transfer_instance_tree"}}),
            gadget.getUrlFor(fast_input_dict)
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            page_title: page_title_translation + " " + gadget.state.doc.title,
            ticket_url: url_list[1],
            destroy_url: url_list[4],
            rss_url: url_list[5],
            selection_url: url_list[6],
            save_action: true
          };
          if (gadget.state.doc.is_owner !== undefined) {
            header_dict.transfer_url = url_list[7];
          }
          if (gadget.state.doc.slap_state === "start_requested") {
            header_dict.stop_url = url_list[3];
          }
          if (gadget.state.doc.slap_state === "stop_requested") {
            header_dict.start_url = url_list[2];
          }
          if (gadget.state.doc.fast_input_dict.enabled !== undefined) {
            header_dict.add_shared_url = url_list[8];
          }
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, jIO, btoa, JSON));
