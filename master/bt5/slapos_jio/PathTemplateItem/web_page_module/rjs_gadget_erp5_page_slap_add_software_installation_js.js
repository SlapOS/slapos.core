/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition('notifySubmit', function () {
      return this.triggerSubmit();
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
        .push(function (doc) {
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              return gadget.jio_getAttachment(doc.relative_url,
                url + doc.relative_url + "/SoftwareRelease_requestSoftwareInstallation?compute_node=" + doc.compute_node);
            });
        })
        .push(function (key) {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'})
            .push(function () {
              // Workaround, find a way to open document without break gadget.
              return gadget.redirect({"command": "change",
                                    "options": {"jio_key": key, "page": "slap_controller"}});
            });
        });
    })


    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "New Software Installation created.",
          "The name of a document in ERP5",
          "Software Release to be Installed",
          "Target Compute Node Title",
          "Target Compute Node Reference",
          "Compute Node",
          "Parent Relative Url",
          "Proceed to Supply Software"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_get(options.jio_key),
            gadget.jio_get(options.compute_node_jio_key),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_translation = result[3][0];
          page_title_translation = result[3][7];
          var doc = result[1],
            compute_node = result[2];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_url_string": {
                  "description": result[3][1],
                  "title": result[3][2],
                  "default": doc.url_string,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_compute_node_title": {
                  "description": result[3][1],
                  "title": result[3][3],
                  "default": compute_node.title,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_compute_node_reference": {
                  "description": result[3][1],
                  "title": result[3][4],
                  "default": compute_node.reference,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "compute_node_reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_compute_node": {
                  "description": result[3][5],
                  "title": result[3][5],
                  "default": options.compute_node_jio_key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "compute_node",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_relative_url": {
                  "description": "",
                  "title": result[3][6],
                  "default": options.jio_key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "relative_url",
                  "hidden": 1,
                  "type": "StringField"
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
                "center",
                [["my_url_string"], ["your_compute_node_title"], ["your_compute_node_reference"],
                  ["your_compute_node"], ["my_relative_url"]]
              ]]
            }
          })
            .push(function () {
              return gadget.updatePanel({
                jio_key: "software_installation_module"
              });
            })
            .push(function () {
              return RSVP.all([
                gadget.getUrlFor({command: 'change', options: {"page": "slap_select_software_release"}})
              ]);
            })
            .push(function (url_list) {
              return gadget.updateHeader({
                page_title: page_title_translation + " " + doc.title + " on " +  compute_node.reference,
                selection_url: url_list[0],
                submit_action: true
              });
            });
        });
    });
}(window, rJS, RSVP));