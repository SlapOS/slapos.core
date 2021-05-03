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
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, news, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (1 || (result.data.rows[i].value.hasOwnProperty("HostingSubscription_getNewsDict"))) {
              value = result.data.rows[i].id;
              news = result.data.rows[i].value.HostingSubscription_getNewsDict;
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
          "The Status",
          "Software Logo"
        ];

      return new RSVP.Queue()
        .push(function () {
          return gadget.jio_getAttachment('hosting_subscription_module', 'view');
        })
        .push(function (result) {
          gadget.hosting_subscription_module_view = result;
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
            ['list_image', result[2][5]]
          ],
            parameter_dict = gadget.hosting_subscription_module_view._embedded._view.listbox,
            form_list = result[0];
          lines_limit = result[1];
          services_translation = result[2][3];
          parameter_dict.title = services_translation;
          parameter_dict.column_list = column_list;
          parameter_dict.search_column_list = column_list;
          parameter_dict.query = "urn:jio:allDocs?query=portal_type%3A%22" +
                    "Hosting Subscription" + "%22%20AND%20validation_state%3Avalidated";
          parameter_dict.lines = lines_limit;
          parameter_dict.sort = [["title", "ascending"]];
          return form_list.render({
            erp5_document: gadget.hosting_subscription_module_view,
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