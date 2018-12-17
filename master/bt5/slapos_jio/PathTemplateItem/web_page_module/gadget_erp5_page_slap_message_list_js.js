/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("setSetting", "setSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("jio_get", "jio_get")


    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, j, tmp, value, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("modification_date")) {
              result.data.rows[i].value.modification_date = {
                css_class: "date_field",
                date_only: 0,
                description: "The Date",
                editable: 0,
                hidden: 0,
                hidden_day_is_last_day: 0,
                "default": result.data.rows[i].value.modification_date,
                key: "modification_date",
                required: 0,
                timezone_style: 0,
                title: "Message Date",
                type: "DateTimeField"
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
            if (result.data.rows[i].value.hasOwnProperty("text_content")) {
              if (result.data.rows[i].value.text_content &&
                  result.data.rows[i].value.text_content.length > 80) {
                result.data.rows[i].value.text_content =
                  result.data.rows[i].value.text_content.slice(0, 80) + " ...";
              }
            }
          }
          return result;
        });
    })
    .declareMethod("triggerSubmit", function () {
      var argument_list = arguments;
      return this.getDeclaredGadget('form_list')
        .push(function (gadget) {
          return gadget.triggerSubmit.apply(gadget, argument_list);
        });
    })
    .declareMethod("render", function (options) {
      var gadget = this,
        lines_limit;

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getSetting("listbox_lines_limit", 20),
            gadget.getSetting("me")
          ]);
        })
        .push(function (setting) {
          lines_limit = setting[0];
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.jio_get(setting[1])
          ]);
        })
        .push(function (result) {
          var column_list = [
            ['title', 'Title'],
            ['modification_date', 'Date'],
            ['source_title', "From"],
            ['text_content', 'Message']
            //['follow_up', 'Ticket']
          ];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_message_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=portal_type%3A%20%28%20" +
                    "%22" + "Web Message" + "%22%2C%20%22" + "Mail Message" +
                    "%22%29%20AND%20%28" + "default_destination_reference" +
                    "%3A" +  result[1].reference + "%29%20AND%20%28" +
                    "simulation_state" + "%3A%20%28%22" + "started" +
                    "%22%2C%22" + "stopped" + "%22%29%29%20AND%20%28" +
                    "follow_up_portal_type" + "%3A%20%28%22" + "Support Request" +
                    "%22%2C%22" + "Upgrade Decision" + "%22%2C%22" +
                    "Regularisation Request" + "%22%29%29%20AND%20%28" +
                    "follow_up_simulation_state" + "%3A%20%28%22" +
                    "validated" + "%22%2C%22" + "suspended" + "%22%2C%22" +
                    "confirmed" + "%22%2C%22" + "started" + "%22%2C%22" +
                    "stopped" + "%22%2C%22" + "%22%29%29",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["modification_date", "Descending"]],
                  "title": "Messages",
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
        .push(function (result) {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_rss_ticket"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slapos"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_rss_critical_ticket"}})
          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: "Messages",
            filter_action: true,
            selection_url: result[1],
            rss_url: result[0],
            critical_url: result[2]
          });
        });
    });
}(window, rJS, RSVP));