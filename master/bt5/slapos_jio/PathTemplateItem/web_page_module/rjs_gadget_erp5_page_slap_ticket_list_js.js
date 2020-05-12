/*global window, rJS, RSVP, document */
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
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

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
    .declareService(function () {
      var helptext = document.getElementById("pagehelp").innerText;
      return this.getDeclaredGadget("pagehelp")
        .push(function (gadget) {
          return gadget.changeState({
            helptext: helptext
          });
        });
    })
    .declareMethod("render", function () {
      var gadget = this,
        lines_limit,
        tickets_translation,
        translation_list = [
          "Title",
          "Reference",
          "State",
          "Tickets"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getSetting("listbox_lines_limit", 20),
            window.getSettingMe(gadget)
          ]);
        })
        .push(function (setting) {
          lines_limit = setting[0];
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.jio_get(setting[1]),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var column_list = [
            ['title', result[2][0]],
            ['reference', result[2][1]],
            ['translated_simulation_state_title', result[2][2]]
          ];
          tickets_translation = result[2][3];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_site_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=portal_type%3A%20%28%22Support%20Request%22%2C%20%22Upgrade%20Decision%22%2C%20%22Regularisation%20Request%22%29%20AND%20destination_decision_reference%3A" +  result[1].reference,
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["modification_date", "Descending"]],
                  "title": tickets_translation,
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
            jio_key: "support_request_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_ticket"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_rss_ticket"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slapos"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_rss_critical_ticket"}})
          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: tickets_translation,
            filter_action: true,
            selection_url: result[2],
            add_url: result[0],
            rss_url: result[1],
            critical_url: result[3]
          });
        });
    });
}(window, rJS, RSVP, document));