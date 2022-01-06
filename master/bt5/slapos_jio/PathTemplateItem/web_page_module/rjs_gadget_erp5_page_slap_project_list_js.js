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
    .declareAcquiredMethod("jio_get", "jio_get")
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
            if (1 || (result.data.rows[i].value.hasOwnProperty("Project_getNewsDict"))) {
              value = result.data.rows[i].id;
              news = result.data.rows[i].value.Project_getNewsDict;
              result.data.rows[i].value.Project_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  "default": {jio_key: value, result: news},
                  key: "status",
                  url: "gadget_slapos_project_status.html",
                  title: "Status",
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
        projects_translation,
        translation_list = [
          "Projects"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.jio_getAttachment('project_module', 'view'),
            gadget.getTranslationList(translation_list)
          ])
        })
        .push(function (result) {
          projects_translation = result[2][0];
          return result[0].render({
            erp5_document: result[1],
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
            jio_key: "project_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_project"}}),
            gadget.getUrlFor({command: "change", options: {"page": "slap_service_list"}})
          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: projects_translation,
            filter_action: true,
            selection_url: result[1],
            add_url: result[0]
          });
        });
    });
}(window, rJS, RSVP));