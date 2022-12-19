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
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("start_date")) {
              value = new Date(result.data.rows[i].value.start_date);
              result.data.rows[i].value.start_date = {
                "field_gadget_param": {
                  allow_empty_time: 0,
                  ampm_time_style: 0,
                  css_class: "date_field",
                  date_only: true,
                  description: "The Date",
                  editable: 0,
                  hidden: 0,
                  hidden_day_is_last_day: 0,
                  "default": value.toUTCString(),
                  key: "date",
                  required: 0,
                  timezone_style: 0,
                  title: "Date",
                  type: "DateTimeField"
                }
              };
            }

            if (result.data.rows[i].value.hasOwnProperty("total_price")) {
              value = window.parseFloat(result.data.rows[i].value.total_price);
              // The field seemms not set precision to display
              value = value.toFixed(2); // round on this case for 2 digits as
                                       // float field is bugged.
              result.data.rows[i].value.total_price = value;
            }
            if (1 || (result.data.rows[i].hasOwnProperty("id"))) {
              value = result.data.rows[i].value.AccountingTransaction_getPaymentStateAsHateoas;
              value.jio_key = result.data.rows[i].id;
              result.data.rows[i].value.AccountingTransaction_getPaymentStateAsHateoas = {
                field_gadget_param : {
                  css_class: "",
                  description: "Payment State",
                  hidden: 0,
                  "default": value,
                  key: "translated_simulation_state_title",
                  url: "gadget_slapos_invoice_state.html",
                  title: "Payment State",
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value.download = {
                field_gadget_param : {
                  css_class: "",
                  description: "Download Invoice",
                  hidden: 0,
                  "default": {jio_key: result.data.rows[i].id},
                  key: "download",
                  url: "gadget_slapos_invoice_printout.html",
                  title: "Download",
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
        invoices_translation,
        translation_list = [
          "Date",
          "Price",
          "Currency",
          "Payment",
          "Download",
          "Invoices",
          "Reference"
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
            ['reference', result[2][6]],
            ['start_date', result[2][0]],
            ['total_price', result[2][1]],
            ['resource_reference', result[2][2]],
            ['AccountingTransaction_getPaymentStateAsHateoas', result[2][3]],
            ['download', result[2][4]]
          ],
            form_list = result[0];
          lines_limit = result[1];
          invoices_translation = result[2][5];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_invoice_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  // XXX FIX ME: Missing default_destination_section_uid=person.getUid()
                  "query": "urn:jio:allDocs?query=(NOT%20title%3A%22Reversal%20Transaction%20for%20%25%22)%20AND%20(portal_type%3A%20%22Sale%20Invoice%20Transaction%22)",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["creation_date", "descending"]],
                  "title": invoices_translation,
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
          return RSVP.all([
            gadget.getSetting("hateoas_url"),
            window.getSettingMe(gadget)
          ]);
        })
        .push(function (url_list) {
          return RSVP.all([
            gadget.jio_getAttachment("contract_relative_url",
              url_list[0] + url_list[1] + "/Person_getCloudContractRelated?return_json=True"),
            gadget.updatePanel({jio_key: "accounting_module"}),
            gadget.getSetting('frontpage_gadget')
          ]);
        })
        .push(function (result) {
          var promise_list = [
            gadget.getUrlFor({command: "change", options: {"page": result[2]}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_rss_ticket",
                                                           "jio_key": "accounting_module"}}),
            gadget.getUrlFor({command: "change", options: {"page": 'slap_invoice_list'}})
          ];
          if (result[0]) {
            promise_list.push(
              gadget.getUrlFor({command: "change", options: {"jio_key": result[0],
                                                           "page": "slap_controller"}})
            );
          }
          return RSVP.all(promise_list);
        })
        .push(function (result) {
          var header_dict = {
            page_title: invoices_translation,
            selection_url: result[0],
            tab_url: result[2],
            rss_url: result[1],
            filter_action: true
          };
          if (result[3]) {
            header_dict.contract_url = result[3];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));
