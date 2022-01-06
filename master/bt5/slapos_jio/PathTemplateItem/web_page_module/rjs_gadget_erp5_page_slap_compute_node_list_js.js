/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("reload", "reload")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("setSetting", "setSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, news, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if ((result.data.rows[i].value.hasOwnProperty("ComputeNode_getNewsDict"))) {
              value = result.data.rows[i].id;
              news = result.data.rows[i].value.ComputeNode_getNewsDict;
              result.data.rows[i].value.ComputeNode_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  "default": {jio_key: value,
                              result: news},
                  key: "status",
                  url: "gadget_slapos_compute_node_status.html",
                  title: "Status",
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


    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod("triggerSubmit", function () {
      var argument_list = arguments;
      return this.getDeclaredGadget('form_list')
        .push(function (gadget) {
          return gadget.triggerSubmit.apply(gadget, argument_list);
        });
    })
    .declareMethod("render", function () {
      var gadget = this,
        default_strict_allocation_scope_uid,
        lines_limit,
        servers_translation,
        translation_list = [
          "Title",
          "Reference",
          "Allocation Scope",
          "Status",
          "Servers"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.getSetting("listbox_lines_limit", 20),
            gadget.jio_get("portal_categories/allocation_scope/close/forever"),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var column_list = [
            ['title', result[3][0]],
            ['reference', result[3][1]],
            ['allocation_scope_title', result[3][2]],
            ['ComputeNode_getNewsDict', result[3][3]]
          ],
            form_list = result[0];
          lines_limit = result[1];
          default_strict_allocation_scope_uid = result[2].uid;
          servers_translation = result[3][4];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_compute_node_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=((portal_type%3A%22Compute%20Node%22)%20AND%20(validation_state%3A%22validated%22)%20AND%20NOT%20(%20default_strict_allocation_scope_uid%3A%20%20" +
                         default_strict_allocation_scope_uid + "%20))",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title": servers_translation,
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
                "bottom",
                [["listbox"]]
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
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_compute_node"}}),
            gadget.getUrlFor({command: "change", options: {page: "slap_compute_node_get_token"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_service_list"}})

          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: servers_translation,
            token_url: result[1],
            selection_url: result[2],
            filter_action: true,
            add_url: result[0]
          });
        });
    });
}(window, rJS, RSVP));