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

    .onStateChange(function () {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Software Release",
          "Software Release Version",
          "Computer Reference",
          "Computer",
          "Reference",
          "State",
          "Usage",
          "Software Release URL",
          "Monitoring Status",
          "Software Installation"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getUrlFor({command: "change", options: {jio_key: gadget.state.doc.aggregate }}),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          page_title_translation = result[2][9];
          var form_gadget = result[0],
            computer_url = result[1];
          return form_gadget.render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_software_release_title": {
                  "description": "",
                  "title": result[2][0],
                  "default": gadget.state.doc.software_release_title,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "software_release_title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_software_release_version": {
                  "description": "",
                  "title": result[2][1],
                  "default": gadget.state.doc.software_release_version,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "software_release_version",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_aggregate_reference": {
                  "description": "",
                  "title": result[2][2],
                  "default": "<a href=" + computer_url + ">" +
                        gadget.state.doc.aggregate_reference + "</a>",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "aggregate_reference",
                  "hidden": 0,
                  "type": "EditorField"
                },
                "my_aggregate_title": {
                  "description": "",
                  "title": result[2][3],
                  "default": "<a href=" + computer_url + ">" +
                    gadget.state.doc.aggregate_title + "</a>",
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "aggregate_title",
                  "hidden": 0,
                  "type": "EditorField"
                },
                "my_reference": {
                  "description": "",
                  "title": result[2][4],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "refeference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_state": {
                  "description": "",
                  "title": result[2][5],
                  "default": gadget.state.doc.state,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "State",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_usage": {
                  "description": "",
                  "title": result[2][6],
                  "default": gadget.state.doc.usage,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "usage",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_url_string": {
                  "description": "",
                  "title": result[2][7],
                  "default": gadget.state.doc.url_string,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_monitoring_status": {
                  "description": "",
                  "title": result[2][8],
                  "default": {jio_key: gadget.state.jio_key},
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_installation_status.html",
                  "sandbox": "",
                  "key": "monitoring_status",
                  "hidden": 0,
                  "type": "GadgetField"
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
                [["my_software_release_title"], ["my_software_release_version"],
                  ["my_reference"]
                  ]
              ], [
                "right",
                [["my_aggregate_title"], ["my_aggregate_reference"], ["my_state"], ["my_usage"]]
              ], [
                "center",
                [["my_url_string"], ['my_monitoring_status']]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "software_installation_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": "slap_destroy_software_installation"}}),
            gadget.getUrlFor({command: 'history_previous'})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: page_title_translation + " : " + gadget.state.doc.software_release_title,
            destroy_url: url_list[0]
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));