/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("reload", "reload")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("setSetting", "setSetting")
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")

    .allowPublicAcquisition("getUrlForList", function (promise_list) {

      var index, param_list, gadget = this;
      for (index in promise_list[0]) {
        if ((promise_list[0][index].command === "index") && (promise_list[0][index].options.jio_key) &&
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
        lines_limit;

      if (options.computer_jio_key !== undefined) {
        gadget.computer_jio_key = options.computer_jio_key;
      }

      return new RSVP.Queue()
        .push(function () {
          return gadget.getSetting("listbox_lines_limit", 100);
        })
        .push(function (listbox_lines_limit) {
          lines_limit = listbox_lines_limit;
          return gadget.getDeclaredGadget('form_list');
        })
        .push(function (form_list) {
          var column_list = [
            ['title', 'Title'],
            ['description', 'Description']
          ];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
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
                  "title": "Software Products",
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
            gadget.getUrlFor({command: 'change', options: {"page": "slap_controller"}})
          ]);
        })
        .push(function (url_list) {
          return gadget.updateHeader({
            page_title: "Select one Software",
            selection_url: url_list[0],
            filter_action: true
          });
        });
    });
}(window, rJS, RSVP));