/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

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
          return gadget.getSetting('frontpage_gadget');
        })
        .push(function (frontpage_gadget) {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_add_project"}}),
            gadget.getUrlFor({command: "change", options: {"page": frontpage_gadget}}),
            gadget.updatePanel({jio_key: "project_module"})
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