/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    message_source = gadget_klass.__template_element
                         .getElementById("message-template")
                         .innerHTML,
    message_template = Handlebars.compile(message_source);

  gadget_klass
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translateHtml", "translateHtml")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .declareMethod("getContent", function () {
      return {};
    })
    .declareMethod("render", function (options) {
      var gadget = this,
        translation_list = [
          "Success...",
          "Fail...",
          "Unknown action to take:"
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getElement(),
            gadget.getUrlFor({command: 'change',
                     options: {jio_key: "/", page: "slapos"}}),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var redirect_url = result[1],
            element = result[0],
            message = options.portal_status_message,
            page_title;
          if (options.message_type === "success") {
            page_title = result[2][0];
          } else if (options.message_type === "error") {
            page_title = result[2][1];
          } else {
            throw new Error(result[2][2] + " " + options.result);
          }
          element.innerHTML = message_template({
            message_to_acknowledge: message,
            redirect_url: redirect_url
          });
          return page_title;
        })
        .push(function (page_title) {
          var header_dict = {
            page_title: page_title
          };
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, Handlebars));