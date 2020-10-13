/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    already_requested_source = gadget_klass.__template_element
                         .getElementById("already-requested-template")
                         .innerHTML,
    already_requested_template = Handlebars.compile(already_requested_source),
    thank_you_source = gadget_klass.__template_element
                         .getElementById("thank-you-template")
                         .innerHTML,
    thank_you_template = Handlebars.compile(thank_you_source),
    exceed_limit_source = gadget_klass.__template_element
                         .getElementById("exceed-limit-template")
                         .innerHTML,
    exceed_limit_template = Handlebars.compile(exceed_limit_source);

  gadget_klass
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
          "Already Requested",
          "Thank You",
          "Limit Exceed",
          "Unknown action to take:"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.updatePanel({
            jio_key: false
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getElement(),
            gadget.getUrlFor({command: 'change',
                     options: {jio_key: "/", page: "trial", "result": ""}}),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var return_url = result[1],
            element = result[0],
            template,
            page_title;

          if (options.result === "already-requested") {
            template = already_requested_template;
            page_title = result[2][0];
          } else if (options.result === "thank-you") {
            template = thank_you_template;
            page_title = result[2][1];
          } else if (options.result === "exceed-limit") {
            template = exceed_limit_template;
            page_title = result[1][2];
          } else {
            throw new Error(result[2][3] + options.result);
          }
          element.innerHTML = template({
            return_url: return_url
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