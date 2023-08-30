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
                                                "shared": doc.shared,
                                                "parameter_output": doc.parameter_output}});
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
      if (options.restricted_softwaretype === undefined) {
        options.restricted_softwaretype = false;
      }
      return this.changeState({
        "url_string": options.url_string,
        "parameter_output": options.parameter_output,
        "software_type": options.software_type,
        "shared": options.shared,
        "restricted_softwaretype": options.restricted_softwaretype
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
          var parameter_hash,
            parameter_dict,
            default_url;

          if (gadget.state.url_string === "") {
            default_url = result[1] + "sample-software-schema/simpledemo/software.cfg";
          } else {
            default_url = gadget.state.url_string;
          }
          if (gadget.state.parameter_output === undefined) {
            parameter_hash = btoa('<?xml version="1.0" encoding="utf-8" ?><instance></instance>');
          } else {
            parameter_hash = btoa(gadget.state.parameter_output);
          }
          parameter_dict = {
            'json_url':  gadget.state.url_string.split('?')[0] + ".json",
            'parameter_hash': parameter_hash,
            'softwaretype': gadget.state.software_type,
            'restricted_softwaretype': false
          };
          if (gadget.state.shared === 'yes') {
            parameter_dict['shared'] = true;
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
                  "editable": 0,
                  "url": "gadget_erp5_page_slap_parameter_form.html",
                  "sandbox": "",
                  "key": "text_content",
                  "hidden": gadget.state.url_string === "",
                  "type": "GadgetField",
                  "renderjs_extra": JSON.stringify(parameter_dict)
                },
                "your_software_type": {
                  "description": "Software Type",
                  "title": "Software Type",
                  "default": "default",
                  "css_class": "",
                  "required": 1,
                  "editable": gadget.state.url_string === "",
                  "key": "software_type",
                  "hidden": gadget.state.url_string !== "",
                  "type": "StringField"
                },
                "your_shared": {
                  "description": "Software Type",
                  "title": "Software Type",
                  "default": "no",
                  "css_class": "",
                  "required": 1,
                  "editable": gadget.state.url_string === "",
                  "key": "shared",
                  "hidden": gadget.state.url_string !== "",
                  "type": "StringField"
                },
                "your_text_content_to_load": {
                  "description": "",
                  "title": "Parameters to Load",
                  "default": '<?xml version="1.0" encoding="utf-8" ?><instance></instance>',
                  "css_class": "",
                  "required": 0,
                  "editable": 1,
                  "sandbox": "",
                  "key": "parameter_output",
                  "hidden": gadget.state.url_string !== "",
                  "type": "TextAreaField"
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
                [["your_url_string"], ["your_software_type"], ["your_shared"], ["your_text_content"], ['your_text_content_to_load']]
              ]]
            }
          })
            .push(function () {
              return gadget.getUrlFor({"command": "change",
                                       "options": {"url_string": undefined,
                                                  "software_type": undefined,
                                                  "shared": undefined,
                                                  "parameter_output": undefined}});
            })
            .push(function (selection_url) {
              var header_dict = {
                page_title: "Parameter testing page",
                selection_url: selection_url              };
              if (gadget.state.parameter_output === undefined) {
                header_dict['submit_action'] = true;
              }
              return gadget.updateHeader(header_dict);
            });
        });
    });
}(window, rJS, RSVP, btoa, JSON));