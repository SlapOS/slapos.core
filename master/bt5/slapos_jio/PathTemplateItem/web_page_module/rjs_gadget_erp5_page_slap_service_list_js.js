/*global window, rJS, RSVP, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP, JSON) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("reload", "reload")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, value_jio_key, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("InstanceTree_getNewsDict")) {
              value_jio_key = result.data.rows[i].id;
              value = result.data.rows[i].value.InstanceTree_getNewsDict;
              result.data.rows[i].value.InstanceTree_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  hidden: 0,
                  default: "",
                  renderjs_extra: JSON.stringify({
                    jio_key: value_jio_key,
                    result: value
                  }),
                  key: "status",
                  url: "gadget_slapos_status.html",
                  type: "GadgetField"
                }
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
        services_translation;

      return new RSVP.Queue()
        .push(function () {
          return gadget.jio_getAttachment('instance_tree_module', 'view');
        })
        .push(function (result) {
          gadget.instance_tree_module_view = result;
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.getSetting("listbox_lines_limit", 20),
            gadget.getTranslationList(["Services"])
          ]);
        })
        .push(function (result) {
          gadget.title_translation = result[2][2];
          gadget.description_translation = result[2][4];
          var form_list = result[0];
          services_translation = result[2][0];
          return form_list.render({
            /**
             * XXX should update every page on Panel
             * Directly use a new created ERP5 form to display the list
             * instead of using hard-corded JS 
            **/
            erp5_document: gadget.instance_tree_module_view,
            form_definition: {
              group_list: [[
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.getSetting('frontpage_gadget');
        })
        .push(function (frontpage_gadget) {
          return RSVP.all([
            gadget.getUrlFor({command: "display_dialog_with_history", options: {"page": "slap_select_software_product"}}),
            gadget.getUrlFor({command: "change", options: {"page": frontpage_gadget}}),
            gadget.updatePanel({jio_key: "instance_tree_module"})
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
}(window, rJS, RSVP, JSON));