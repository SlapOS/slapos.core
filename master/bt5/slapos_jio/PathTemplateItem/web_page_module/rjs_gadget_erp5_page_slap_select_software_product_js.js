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
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("getUrlForList", function (promise_list) {

      var index, gadget = this;
      for (index in promise_list[0]) {
        if ((promise_list[0].hasOwnProperty(index)) &&
            (promise_list[0][index].command === "display_with_history_and_cancel") && (promise_list[0][index].options.jio_key) &&
            (promise_list[0][index].options.jio_key.startsWith("software_product_module"))) {
          promise_list[0][index].options.page = "slap_select_software_release";
          if (gadget.computer_jio_key !== undefined) {
            promise_list[0][index].options.computer_jio_key = gadget.computer_jio_key;
          }
        }
      }
      return gadget.getUrlForList(promise_list[0]);
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
    .declareMethod("render", function (options) {
      var gadget = this,
        lines_limit,
        page_title_translation,
        translation_list = [
          "Title",
          "Description",
          "Software Products",
          "1/3 Select one Software"
        ];

      if (options.computer_jio_key !== undefined) {
        gadget.computer_jio_key = options.computer_jio_key;
      }

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.getSetting("listbox_lines_limit", 100),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var form_list = result[0],
            column_list = [
              ['title', result[2][0]],
              ['description', result[2][1]]
            ];
          lines_limit = result[1];
          page_title_translation = result[2][3];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "command": 'display_with_history_and_cancel',
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_software_product_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Software Product" + "%22%20AND%20validation_state%3Apublished",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title": result[2][2],
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
            jio_key: "software_product_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'cancel_dialog_with_history'})
          ]);
        })
        .push(function (url_list) {
          return gadget.updateHeader({
            page_title: page_title_translation,
            cancel_url: url_list[0],
            filter_action: true
          });
        });
    });
}(window, rJS, RSVP));