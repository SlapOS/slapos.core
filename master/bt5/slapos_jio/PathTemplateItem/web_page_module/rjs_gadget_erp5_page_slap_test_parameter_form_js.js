/*global window, rJS, RSVP, btoa, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3, sub:true */
(function (window, rJS, RSVP, btoa, JSON) {
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
            return gadget.notifySubmitted({message: "Doc is empty", status: 'error'});
          }
          return gadget.getSetting("hateoas_url")
            .push(function () {
              return gadget.notifySubmitted({message: "All is fine, we reseted your form.", status: 'success'})
                .push(function () {
                  return gadget.redirect({"command": "change",
                                    "options": {"url_string": doc.url_string,
                                                "software_type": doc.software_type,
                                                "parameter_output": doc.text_content}});
                });
            }, function (error) {
              if (error.target.status === 409) {
                return gadget.notifySubmitted({message: "Error 409", status: 'error'});
              }
              if (error.target.status === 400) {
                return gadget.notifySubmitted({message: "Error 400", status: 'error'});
              }
            });
        });
    })

    .declareMethod("triggerSubmit", function () {
      // @ts-ignore
      return this.element.querySelector('button[type="submit"]').click();
    })

    .declareMethod("render", function (options) {
      if (options.url_string === undefined) {
        options.url_string = "";
      }
      return this.changeState({
        "url_string": options.url_string,
        "parameter_output": options.parameter_output,
        "software_type_list": options.software_type
      });
    })

    .onStateChange(function onStateChange() {
      var gadget = this;
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getSetting("hateoas_url")
          ]);
        })
        .push(function (result) {
          var parameter_xml,
            parameter_dict,
            default_url;

          if (gadget.state.url_string === "") {
            default_url = result[1] + "sample-software-schema/simpledemo/software.cfg";
          } else {
            default_url = gadget.state.url_string;
          }
          if (gadget.state.parameter_output === undefined) {
            parameter_xml = '<?xml version="1.0" encoding="utf-8" ?><instance></instance>';
          } else {
            parameter_xml = gadget.state.parameter_output;
          }
          parameter_dict = {
            'json_url':  gadget.state.url_string.split('?')[0] + ".json",
            'parameter_xml': parameter_xml,
            'software_type_list': []
          };
          if (gadget.state.software_type_list) {
            parameter_dict.software_type_list = gadget.state.software_type_list.split(',');
          }
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "your_url_string": {
                  "description": "Software Release Url",
                  "title": "Software Release URL",
                  "default": default_url,
                  "css_class": "",
                  "required": 1,
                  "editable": gadget.state.url_string === "",
                  "key": "url_string",
                  "hidden": 0,
                  "type": "StringField"
                },
                "your_text_content": {
                  "description": "",
                  "title": "Parameters",
                  "default": "",
                  "css_class": "",
                  "required": 1,
                  "editable": gadget.state.url_string !== "",
                  "url": "gadget_erp5_page_slap_parameter_form.html",
                  "sandbox": "",
                  "key": "text_content",
                  "hidden": gadget.state.url_string === "",
                  "type": "GadgetField",
                  "renderjs_extra": JSON.stringify(parameter_dict)
                },
                "your_software_type": {
                  "description": "",
                  "title": "Software type",
                  "default": gadget.state.software_type_list,
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "sandbox": "",
                  "key": "software_type",
                  "hidden": 1,
                  "type": "StringField"
                },
                "your_parameter_output": {
                  "description": "",
                  "title": "Parameters Output",
                  "default": gadget.state.parameter_output,
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "sandbox": "",
                  "key": "parameter_output",
                  "hidden": gadget.state.parameter_output === undefined,
                  "type": "TextAreaField"
                },
                "your_parameter_hash": {
                  "description": "",
                  "title": "Parameters Hash",
                  "default": btoa(parameter_xml),
                  "css_class": "",
                  "required": 0,
                  "editable": 0,
                  "sandbox": "",
                  "key": "parameter_hash",
                  "hidden": gadget.state.parameter_output === undefined,
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
                [["your_url_string"], ["your_parameter_output"], ["your_software_type"], ["your_parameter_hash"], ["your_text_content"]]
              ]]
            }
          })
            .push(function () {
              return gadget.getUrlFor({"command": "change",
                                       "options": {"url_string": undefined,
                                                   "software_type": undefined,
                                                   "parameter_output": undefined}});
            })
            .push(function (selection_url) {
              return gadget.updateHeader({
                page_title: "Parameter testing page",
                selection_url: selection_url,
                submit_action: true
              });
            });
        });
    });
}(window, rJS, RSVP, btoa, JSON));