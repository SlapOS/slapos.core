/*global window, rJS, RSVP, btoa, jIO, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3, sub:true */
(function (window, rJS, RSVP, btoa, jIO, JSON) {
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
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
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
          return form_gadget.checkValidity()
            .push(function (is_valid) {
              if (!is_valid) {
                return null;
              }
              return form_gadget.getContent();
            });
        })
        .push(function (doc) {
          if (doc === null) {
            return gadget.notifySubmitted({message: gadget.message1_translation, status: 'error'});
          }
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              return gadget.jio_putAttachment(doc.relative_url,
                url + doc.relative_url + "/SoftwareRelease_requestInstanceTree", doc);
            })

            .push(function (attachment) {
              return new RSVP.Queue()
                .push(function () {
                  return jIO.util.readBlobAsText(attachment.target.response);
                })
                .push(function (response) {
                  return JSON.parse(response.target.result);
                })
                .push(function (relative_url) {
                  return gadget.notifySubmitted({message: gadget.message2_translation, status: 'success'})
                    .push(function () {
                    // Workaround, find a way to open document without break gadget.
                      return gadget.redirect({"command": "change",
                                    "options": {"jio_key": relative_url, "page": "slap_controller"}});
                    });
                });
            }, function (error) {
              if (error.target.status === 409) {
                return gadget.notifySubmitted({message: gadget.message3_translation, status: 'error'});
              }
              if (error.target.status === 400) {
                return gadget.notifySubmitted({message: gadget.message4_translation, status: 'error'});
              }
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
          "Please review the form.",
          "New service created.",
          "The name of a document in ERP5",
          "Software Release URL",
          "Title",
          "Instance Parameter",
          "Compute Node",
          "SLA",
          "Parent Relative Url",
          "3/3 Request Service:",
          "A service with this title already exists.",
          "Service Title is mandatory."
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_get(options.jio_key),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message1_translation = result[2][0];
          gadget.message2_translation = result[2][1];
          gadget.message3_translation = result[2][10];
          gadget.message4_translation = result[2][11];
          page_title_translation = result[2][9];
          var doc = result[1],
            parameter_dict = {
              'json_url':  doc.url_string.split('?')[0] + ".json",
              'parameter_xml': '<?xml version="1.0" encoding="utf-8" ?><instance/>'
            };
          if (options.software_type) {
            parameter_dict['softwaretype'] = options.software_type;
          }
          if (options.shared) {
            parameter_dict['shared'] = true;
          }

          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_url_string": {
                  "description": result[2][2],
                  "title": result[2][3],
                  "default": doc.url_string,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "url_string",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_title": {
                  "description": result[2][2],
                  "title": result[2][4],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_text_content": {
                  "description": "",
                  "title": result[2][5],
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "url": "gadget_erp5_page_slap_parameter_form.html",
                  "sandbox": "",
                  "key": "text_content",
                  "hidden": 0,
                  "type": "GadgetField",
                  "renderjs_extra": JSON.stringify(parameter_dict)
                },
                "your_computer_guid": {
                  "description": result[2][2],
                  "title": result[2][6],
                  "default": "",
                  "items": doc.computer_guid,
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "key": "computer_guid",
                  "hidden": options.sla_xml !== undefined ? 1 : 0,
                  "type": "ListField"
                },
                "your_sla_xml": {
                  "description": result[2][2],
                  "title": result[2][7],
                  "default": options.sla_xml,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "key": "sla_xml",
                  "hidden": options.sla_xml !== undefined ? 0 : 1,
                  "type": "StringField"
                },
                "my_relative_url": {
                  "description": "",
                  "title": result[2][8],
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
                [["my_url_string"], ["your_title"], ["your_text_content"],
                  ["your_computer_guid"], ["your_sla_xml"], ["my_portal_type"], ["my_relative_url"]]
              ]]
            }
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
                page_title: page_title_translation + " " + doc.title,
                cancel_url: url_list[0],
                submit_action: true
              });
            });
        });
    });
}(window, rJS, RSVP, btoa, jIO, JSON));