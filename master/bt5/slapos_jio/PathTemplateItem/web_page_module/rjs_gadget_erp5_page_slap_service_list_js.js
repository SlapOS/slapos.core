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
      param_list[0].select_list = ["uid", "title", "short_title",
                                   "root_slave", "list_image_url"];
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, news, len = result.data.total_rows, list_image_url_value, list_image_url;
          for (i = 0; i < len; i += 1) {
            if (1 || (result.data.rows[i].value.hasOwnProperty("HostingSubscription_getNewsDict"))) {
              value = result.data.rows[i].id;
              news = result.data.rows[i].value.HostingSubscription_getNewsDict;
              list_image_url = result.data.rows[i].value.list_image_url;
              list_image_url_value = list_image_url ? list_image_url.split("/software_product_module") : null;
              result.data.rows[i].value.HostingSubscription_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: gadget.description_translation,
                  hidden: 0,
                  default: {jio_key: value, result: news},
                  key: "status",
                  url: "gadget_slapos_hosting_subscription_status.html",
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
            result.data.rows[i].value.HostingSubscription_getDefaultImageRelativeUrl = {
              field_gadget_param : {
                description: "image",
                hidden: 0,
                default: list_image_url_value ? ('./software_product_module' + list_image_url_value.pop() + '?quality=75.0&display=thumbnail&format=png') : ("./preview_icon.png"),
                key: "list_image_url",
                title: "IMG",
                type: "ImageField"
              }
            };
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
        services_translation,
        translation_list = [
          "Title",
          "Short Title",
          "Status",
          "Services",
          "The Status"
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
          gadget.title_translation = result[2][2];
          gadget.description_translation = result[2][4];
          var column_list = [
            ['title', result[2][0]],
            ['short_title', result[2][1]],
            ['HostingSubscription_getNewsDict', result[2][2]],
            ['HostingSubscription_getDefaultImageRelativeUrl', 'Image']
          ],
            form_list = result[0];
          lines_limit = result[1];
          services_translation = result[2][3];
          return form_list.render({
            erp5_document: {
              "_embedded": {"_view": {
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_service_listbox",
                  "lines": lines_limit,
                  "list_method": "portal_catalog",
                  // XXX TODO Filter by   default_strict_allocation_scope_uid="!=%s" % context.getPortalObject().portal_categories.allocation_scope.close.forever.getUid(),
                  "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Hosting Subscription" + "%22%20AND%20validation_state%3Avalidated",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title": services_translation,
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
            jio_key: "hosting_subscription_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "display_dialog_with_history", options: {"page": "slap_select_software_product"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slapos"}})

          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: services_translation,
            filter_action: true,
            add_url: result[0],
            selection_url: result[1]
          });
        });
    });
}(window, rJS, RSVP));