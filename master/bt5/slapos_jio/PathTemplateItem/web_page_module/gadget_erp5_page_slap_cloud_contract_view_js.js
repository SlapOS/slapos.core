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
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_put", "jio_put")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (1 || (result.data.rows[i].value.hasOwnProperty("price_currency_title"))) {
              value = result.data.rows[i].value.price_currency_title;
              result.data.rows[i].value.price_currency_title = {
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
              value = result.data.rows[i].value.maximum_invoice_credit;
              result.data.rows[i].value.maximum_invoice_credit = {
                field_gadget_param : {
                  css_class: "",
                  "default": value ? value.toString() : "0.0",
                  key: "status",
                  editable: 1,
                  url: "gadget_slapos_label_listbox_field.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              value = result.data.rows[i].value.CloudContractLine_getRemainingInvoiceCredit;
              result.data.rows[i].value.CloudContractLine_getRemainingInvoiceCredit = {
                field_gadget_param : {
                  css_class: "",
                  "default": value ? value.toString() : "0.0",
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

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod("render", function (options) {
      return this.changeState({
        jio_key: options.jio_key,
        doc: options.doc,
        editable: 1
      });
    })

    .onStateChange(function () {
      var gadget = this,
        translation_list = [
          "Maximum Invoice Delay",
          "Maximum Credit",
          "Cloud Contract",
          "Currency",
          "Maximum Credit per Currency",
          "Remaining Credit"
        ];
      return gadget.getSetting("hateoas_url")
        .push(function (url) {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.account_translation = result[1][2];
          var form_gadget = result[0],
            column_list = [
              ['price_currency_title', result[1][3]],
              ['maximum_invoice_credit', result[1][1]],
              ['CloudContractLine_getRemainingInvoiceCredit', result[1][5]]
            ];
          return form_gadget.render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_maximum_invoice_delay": {
                  "description": "",
                  "title": result[1][0],
                  "default": gadget.state.doc.maximum_invoice_delay,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "maximum_invoice_delay",
                  "hidden": 0,
                  "type": "FloatField"
                },
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 1,
                  "editable_column_list": [],
                  "key": "slap_cloud_contract_line_listbox",
                  "lines": 20,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=%28portal_type%3A%28%22" +
                    "Cloud Contract Line" + "%22%29%29",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [],
                  "title": result[1][4],
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
                [["my_maximum_invoice_delay"]]
              ], [
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: false
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({ command: 'change', options: { page: 'slap_person_view', jio_key: '' } })
          ]);
        })
        .push(function (result) {
          var header_dict = {
            page_title: gadget.account_translation + " : " + gadget.state.doc.destination_section_title,
            selection_url: result[0]
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));