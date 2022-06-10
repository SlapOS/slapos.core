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
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, news, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("ComputerNetwork_getNewsDict")) {
              value = result.data.rows[i].id;
              news = result.data.rows[i].value.ComputerNetwork_getNewsDict;
              result.data.rows[i].value.ComputerNetwork_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  "default": {jio_key: value,
                              result: news},
                  key: "status",
                  url: "gadget_slapos_status.html",
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
        lines_limit,
        networks_translation,
        translation_list = [
          "Title",
          "Reference",
          "Status",
          "Networks"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.getSetting("listbox_lines_limit", 20),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var column_list = [
            ['title', result[2][0]],
            ['reference', result[2][1]],
            ['ComputerNetwork_getNewsDict', result[2][2]]
          ],
            form_list = result[0];
          lines_limit = result[1];
          networks_translation = result[2][3];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_network_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  // Filter by My Own networks
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Computer Network%22%20AND%20validation_state%3Avalidated",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["reference", "ascending"]],
                  "title": networks_translation,
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
            jio_key: "computer_network_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_network"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slapos"}})
          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: networks_translation,
            filter_action: true,
            selection_url: result[1],
            add_url: result[0]
          });
        });
    });
}(window, rJS, RSVP));