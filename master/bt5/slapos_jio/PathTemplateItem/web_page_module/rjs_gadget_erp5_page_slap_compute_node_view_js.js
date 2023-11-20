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
          var i, value, value_jio_key, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.getAccessStatus) {
              value = result.data.rows[i].value.getAccessStatus;
              value_jio_key = result.data.rows[i].id;
              result.data.rows[i].value.getAccessStatus = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  "default": "",
                  renderjs_extra: JSON.stringify({
                    jio_key: value_jio_key,
                    result: value
                  }),
                  key: "status",
                  url: "gadget_slapos_status.html",
                  title: "Status",
                  type: "GadgetField"
                }
              };
            }
            result.data.rows[i].value["listbox_uid:list"] = {
              key: "listbox_uid:list",
              value: 2713
            };
          }
          return result;
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

    .declareMethod("render", function (options) {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Data updated.",
          "Software Release",
          "Url",
          "Status",
          "Title",
          "Reference",
          "Modification Date",
          "State",
          "Enabled",
          "Disabled",
          "Auto Upgrade",
          "Ask Confirmation before Upgrade",
          "Never Upgrade",
          "Closed for maintenance",
          "Closed for termination",
          "Closed forever",
          "Closed outdated",
          "Open for Friends only", // Not used anymore
          "Open",
          "Open Public",
          "Open for Subscribers only",
          "Network",
          "Allocation Scope",
          "Monitoring",
          "Your Friends email", // Not used anymore
          "Upgrade",
          "The name of a document in ERP5",
          "Current Site",
          "Current Project",
          "Monitoring Status",
          "Supplied Softwares",
          "Compute Node:",
          "Associated Tickets",
          "Closed by user"
        ];

      // Follow up changeState API but it is requires to actually
      // re-render the form to hide allocation scope
      gadget.state = {
        jio_key: options.jio_key,
        doc: options.doc,
        editable: 1
      };
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_allDocs({
              query: '(portal_type:"Computer Network") AND (validation_state:validated)',
              sort_on: [['reference', 'ascending']],
              select_list: ['reference', 'title'],
              limit: 100
            }),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (results) {
          gadget.message_translation = results[2][0];
          page_title_translation = results[2][31];
          var form_gadget = results[0],
            computer_network_list = [["", ""]],
            column_list = [
              ['SoftwareInstallation_getSoftwareReleaseInformation', results[2][1]],
              ['url_string', results[2][2]],
              ['getAccessStatus', results[2][3]]
            ],
            ticket_column_list = [
              ['title', results[2][4]],
              ['reference', results[2][5]],
              ['modification_date', results[2][6]],
              ['translated_simulation_state_title', results[2][7]]
            ],
            monitor_scope_list = [['', ''],
                                [results[2][8], 'enabled'],
                                [results[2][9], 'disabled']],
            upgrade_scope_list = [['', ''],
                                [results[2][10], 'auto'],
                                [results[2][11], 'ask_confirmation'],
                                [results[2][12], 'never']],
            supported_allocation_scope_list = ['',
                                'close/maintenance',
                                'close/termination',
                                'close/forever',
                                'close/outdated',
                                'close/noallocation',
                                'open/personal'],
            allocation_scope_list = [['', ''],
                                [results[2][13], 'close/maintenance'],
                                [results[2][14], 'close/termination'],
                                [results[2][15], 'close/forever'],
                                [results[2][16], 'close/outdated'],
                                [results[2][33], 'close/noallocation'],
                                [results[2][18], 'open/personal']],
            i,
            hidden_allocation_scope = {'open/public': results[2][19],
                                       'open/subscription': results[2][20]},
            len = results[1].data.total_rows;


          for (i = 0; i < len; i += 1) {
            computer_network_list.push([
              results[1].data.rows[i].value.title || results[1].data.rows[i].value.reference,
              results[1].data.rows[i].id
            ]);
          }

          if (!supported_allocation_scope_list.includes(
              gadget.state.doc.allocation_scope
            ) && (hidden_allocation_scope.hasOwnProperty(gadget.state.doc.allocation_scope))) {
            allocation_scope_list.push(
              [hidden_allocation_scope[gadget.state.doc.allocation_scope],
                gadget.state.doc.allocation_scope
                ]
            );
          }

          return form_gadget.render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": "",
                  "title": results[2][4],
                  "default": gadget.state.doc.title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": "",
                  "title": results[2][5],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_subordination": {
                  "description": "",
                  "title": results[2][21],
                  "default": gadget.state.doc.subordination,
                  "css_class": "",
                  "items": computer_network_list,
                  "required": 0,
                  "editable": 1,
                  "key": "subordination",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_allocation_scope": {
                  "description": "",
                  "title": results[2][22],
                  "default": gadget.state.doc.allocation_scope,
                  "css_class": "",
                  "items": allocation_scope_list,
                  "required": 0,
                  "editable": 1,
                  "key": "allocation_scope",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_monitor_scope": {
                  "description": "",
                  "title": results[2][23],
                  "default": gadget.state.doc.monitor_scope,
                  "css_class": "",
                  "items": monitor_scope_list,
                  "required": 0,
                  "editable": 1,
                  "key": "monitor_scope",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_upgrade_scope": {
                  "description": "",
                  "title": results[2][25],
                  "default": gadget.state.doc.upgrade_scope,
                  "css_class": "",
                  "items": upgrade_scope_list,
                  "required": 0,
                  "editable": 1,
                  "key": "upgrade_scope",
                  "hidden": 0,
                  "type": "ListField"
                },
                "my_source": {
                  "description": results[2][26],
                  "title": results[2][27],
                  "default": gadget.state.doc.source_title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "",
                  "hidden": gadget.state.doc.source_title ? 0 : 1,
                  "type": "StringField"
                },
                "my_source_project": {
                  "description": results[2][26],
                  "title": results[2][28],
                  "default": gadget.state.doc.source_project_title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "",
                  "hidden": gadget.state.doc.source_project_title ? 0 : 1,
                  "type": "StringField"
                },
                "my_monitoring_status": {
                  "description": "",
                  "title": results[2][29],
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
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_software_installation_listbox",
                  "lines": 10,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Software Installation" + "%22%20AND%20validation_state%3A%22validated%22%20AND%20default_aggregate_reference%3A" +
                    gadget.state.doc.reference,
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title":  results[2][30],
                  "type": "ListBox"
                },
                "ticket_listbox": {
                  "column_list": ticket_column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_project_compute_node_listbox",
                  "lines": 10,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=%28%28portal_type%3A%22" +
                    "Support Request" + "%22%29%20AND%20%28" +
                    "default_aggregate_reference%3A%22" +
                    gadget.state.doc.reference + "%22%29%29",
                  "portal_type": [],
                  "search_column_list": ticket_column_list,
                  "sort_column_list": ticket_column_list,
                  "sort": [["title", "ascending"]],
                  "title": results[2][32],
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
                [["my_title"], ["my_reference"], ["my_subordination"],
                  ['my_monitoring_status']]
              ], [
                "right",
                [["my_source"], ["my_source_project"], ["my_monitor_scope"],
                  ["my_upgrade_scope"], ["my_allocation_scope"]]
              ], [
                "bottom",
                [["ticket_listbox"], ["listbox"]]
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
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_related_ticket"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_select_software_product", 'compute_node_jio_key': gadget.state.jio_key}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_compute_node_request_certificate"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_compute_node_revoke_certificate"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_rss_ticket"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_transfer_compute_node"}}),
            gadget.getUrlFor({command: 'history_previous'})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            page_title: page_title_translation + " " + gadget.state.doc.title,
            ticket_url: url_list[1],
            supply_url: url_list[2],
            rss_url: url_list[5],
            selection_url: url_list[7],
            save_action: true
          };
          if (gadget.state.doc.is_owner !== undefined) {
            header_dict.transfer_url = url_list[6];
            header_dict.request_certificate_url = url_list[3];
            header_dict.revoke_certificate_url = url_list[4];
          }
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, JSON));