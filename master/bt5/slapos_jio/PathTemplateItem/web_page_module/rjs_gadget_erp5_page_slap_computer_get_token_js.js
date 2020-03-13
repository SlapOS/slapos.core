/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("translate", "translate")
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
                url + doc.relative_url + "/Base_getComputerToken");
            })
            .push(function (result) {
              var msg;
              if (result) {
                msg = gadget.msg_translation;
              }
              return gadget.notifySubmitted({message: msg, status: 'success'})
                .push(function () {
                  // Workaround, find a way to open document without break gadget.
                  result.jio_key = doc.relative_url;
                  return gadget.render(result);
                });
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
          "Parent Relative Url",
          "Command Line to Run",
          "SlapOS Master API",
          "SlapOS Master Web UI",
          "Your Token",
          "Request New Token",
          "Token is Requested."
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          page_title_translation = result[1][5];
          gadget.msg_translation = result[1][6];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_relative_url": {
                  "description": "",
                  "title": result[1][0],
                  "default": "computer_module",
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "relative_url",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_command_line": {
                  "description": "",
                  "title": result[1][1],
                  "default": options.command_line,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "command_line",
                  "hidden": (options.access_token === undefined) ? 1 : 0,
                  "type": "StringField"
                },
                "my_slapos_master_api": {
                  "description": "",
                  "title": result[1][2],
                  "default": options.slapos_master_api,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "slapos_master_api",
                  "hidden": (options.access_token === undefined) ? 1 : 0,
                  "type": "StringField"
                },
                "my_slapos_master_web": {
                  "description": "",
                  "title": result[1][3],
                  "default": options.slapos_master_web,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "slapos_master_web",
                  "hidden": (options.access_token === undefined) ? 1 : 0,
                  "type": "StringField"
                },
                "my_access_token": {
                  "description": "",
                  "title": result[1][4],
                  "default": options.access_token,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "certificate",
                  "hidden": (options.access_token === undefined) ? 1 : 0,
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
                [["my_command_line"], ["my_slapos_master_api"], ["my_slapos_master_web"], ["my_access_token"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'change', options: {page: "slap_computer_list"}})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            page_title: page_title_translation,
            submit_action: true,
            selection_url: url_list[0]
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP));