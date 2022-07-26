/*globals console, window, rJS, RSVP, loopEventListener, i18n, domsugar, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, domsugar) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translateHtml", "translateHtml")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .declareMethod("getContent", function () {
      return {};
    })
    .declareMethod("render", function (options) {
      var gadget = this,
        translation_list = [
          "Success...",
          "Fail...",
          "Unknown action to take:",
          "Continue"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.updatePanel({
            jio_key: false
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: 'change',
                     options: {jio_key: "/", page: "slapos"}}),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var redirect_url = result[0],
            message = options.portal_status_message,
            page_title;
          if (options.message_type === "success") {
            page_title = result[1][0];
          } else if (options.message_type === "error") {
            page_title = result[1][1];
          } else {
            throw new Error(result[1][2] + " " + options.result);
          }
          domsugar(gadget.element,
            {},
            [
              domsugar("p", {}, [
                domsugar("center", {}, [
                  domsugar("strong", {text: message})
                ])
              ]),
              domsugar("p"),
              domsugar("p", {}, [
                domsugar("center", {}, [
                  domsugar("a", {
                    text: result[1][3],
                    "data-i18n": "Continue",
                    href: redirect_url,
                    class: "ui-btn ui-first-child ui-btn-icon-center"
                  })
                ])
              ])
            ]);
          return page_title;
        })
        .push(function (page_title) {
          var header_dict = {
            page_title: page_title
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, domsugar));