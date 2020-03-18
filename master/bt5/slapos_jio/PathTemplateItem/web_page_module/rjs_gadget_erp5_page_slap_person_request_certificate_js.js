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
                url + doc.relative_url + "/Person_getCertificate");
            })
            .push(function (result) {
              var msg;
              if (result) {
                msg = gadget.msg1_translation;
              } else {
                msg = gadget.msg2_translation;
                result = {};
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
          "Certificate is Requested.",
          "This person already has one certificate, please revoke it before request a new one..",
          "Parent Relative Url",
          "Your Certificate",
          "Your Key",
          "Request New Certificate"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.msg1_translation = result[1][0];
          gadget.msg2_translation = result[1][1];
          page_title_translation = result[1][5];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_relative_url": {
                  "description": "",
                  "title": result[1][2],
                  "default": options.jio_key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "relative_url",
                  "hidden": 1,
                  "type": "StringField"
                },
                "my_certificate": {
                  "description": "",
                  "title": result[1][3],
                  "default": options.certificate,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "certificate",
                  "hidden": (options.certificate === undefined) ? 1 : 0,
                  "type": "TextAreaField"
                },
                "my_key": {
                  "description": "",
                  "title": result[1][4],
                  "default": options.key,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "key",
                  "hidden": (options.key === undefined) ? 1 : 0,
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
                [["my_key"], ["my_certificate"], ["my_relative_url"]]
              ]]
            }
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'change', options: {page: 'slap_person_view'}})
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