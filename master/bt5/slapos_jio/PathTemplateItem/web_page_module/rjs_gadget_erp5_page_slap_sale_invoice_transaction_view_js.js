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
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

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
          "The Date",
          "Date",
          "Reference",
          "Total",
          "Currency",
          "Payment State",
          "Download",
          "Invoice:",
          "Data updated.",
          "Instance",
          "From",
          "To",
          "Quantity",
          "Payment Receipt Reference"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list),
            gadget.getSetting("hateoas_url")
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[1][8];
          page_title_translation = result[1][7];
          var form_gadget = result[0],
            column_list = [
              ["title", result[1][9]],
              ["start_date", result[1][10]],
              ["stop_date", result[1][11]],
              ["quantity", result[1][12]]
            ],
            start_date = new Date(gadget.state.doc.start_date),
            total_price = window.parseFloat(gadget.state.doc.total_price).toFixed(2);
          return form_gadget.render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_start_date": {
                  "allow_empty_time": 0,
                  "ampm_time_style": 0,
                  "css_class": "date_field",
                  "date_only": 1,
                  "description": result[1][0],
                  "editable": 0,
                  "hidden": 0,
                  "hidden_day_is_last_day": 0,
                  "default": start_date.toUTCString(),
                  "key": "date",
                  "required": 0,
                  "timezone_style": 0,
                  "title": result[1][1],
                  "type": "DateTimeField"
                },
                "my_reference": {
                  "description": "",
                  "title": result[1][2],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_payment_transaction_external_id": {
                  "description": "",
                  "title": result[1][13],
                  "default": gadget.state.doc.payment_transaction_external_id,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "payment_transaction_external_id",
                  "hidden": gadget.state.doc.payment_transaction_external_id === "",
                  "type": "StringField"
                },
                "my_total_price": {
                  "description": "",
                  "title": result[1][3],
                  "default": total_price,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "total_price",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_resource_title": {
                  "description": "",
                  "title": result[1][4],
                  "default": gadget.state.doc.resource_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "resource_title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_payment_state": {
                  "description": "",
                  "title": result[1][5],
                  "default": {
                    state: gadget.state.doc.payment_state,
                    jio_key: gadget.state.jio_key
                  },
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_invoice_state.html",
                  "sandbox": "",
                  "key": "payment_state",
                  "hidden": 0,
                  "type": "GadgetField"
                },
                "my_download": {
                  "description": "",
                  "title": result[1][6],
                  "default": {jio_key: gadget.state.jio_key},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_invoice_printout.html",
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
                  "editable_column_list": column_list,
                  "key": "listbox",
                  "lines": 20,
                  "list_method": "SaleInvoiceTransaction_getRelatedInstanceTreeReportLineList",
                  "list_method_template": result[2] + gadget.state.jio_key + "/ERP5Document_getHateoas?mode=search&" +
                    "list_method=SaleInvoiceTransaction_getRelatedInstanceTreeReportLineList" +
                    "{&query,select_list*,limit*,sort_on*,local_roles*}",
                  "query": "urn:jio:allDocs?query=",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["start_date", "ASC"]],
                  "title": "Subscriptions",
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
                [["my_start_date"], ["my_reference"], ["my_total_price"],
                  ["my_resource_title"], ["my_download"]]
              ],[
                "right",
                [["my_payment_transaction_external_id"], ['my_payment_state']]
              ],[
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "accounting_module"
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
              page_title: page_title_translation + ' ' + gadget.state.doc.reference
            };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));