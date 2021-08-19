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
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("getUrlForList", function (promise_list) {

      var index, gadget = this;
      for (index in promise_list[0]) {
        if ((promise_list[0].hasOwnProperty(index)) &&
            (promise_list[0][index].command === "display_with_history_and_cancel") && (promise_list[0][index].options.jio_key) &&
            (promise_list[0][index].options.jio_key.startsWith("software_release_module"))) {
          if (gadget.compute_node_jio_key !== undefined) {
            promise_list[0][index].options.page = "slap_add_software_installation";
            promise_list[0][index].options.compute_node_jio_key = gadget.compute_node_jio_key;
          } else {
            promise_list[0][index].options.page = "slap_add_instance_tree";
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
        page_title_translation,
        translation_list = [
          "Title",
          "Version",
          "Description",
          "Software Releases",
          "2/3 Select one Release"
        ];

      if (options.compute_node_jio_key !== undefined) {
        gadget.compute_node_jio_key = options.compute_node_jio_key;
      }
      return gadget.jio_get(options.jio_key)
        .push(function (doc) {
          return new RSVP.Queue()
            .push(function () {
              return RSVP.all([
                gadget.getDeclaredGadget('form_list'),
                gadget.getTranslationList(translation_list)
              ]);
            })
            .push(function (result) {
              var form_list = result[0],
                column_list = [
                  ['title', result[1][0]],
                  ['version', result[1][1]],
                  ['description', result[1][2]]
                ];
              page_title_translation = result[1][4];
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
                      "lines": 15,
                      "list_method": "portal_catalog",
                      "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                        "Software Release" + "%22%20AND%20" +
                         "validation_state%3A" +
                         "%28%22shared%22%2C" +
                         "%22shared_alive%22%2C" +
                         "%20%22released%22%3B%20" +
                         "%22released_alive%22%2C" +
                         "%22published%22%2C" +
                         "%22published_alive%22%29" +
                         "%20AND%20default_aggregate_reference%3A" +
                         doc.reference,
                      "portal_type": [],
                      "search_column_list": column_list,
                      "sort_column_list": column_list,
                      "sort": [["title", "ascending"]],
                      "title": result[1][3],
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
            });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "software_release_module"
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