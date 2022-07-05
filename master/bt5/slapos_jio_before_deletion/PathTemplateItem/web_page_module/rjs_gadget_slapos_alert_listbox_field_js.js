/*globals console, document, window, rJS */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (document, window, rJS, domsugar) {
  "use strict";
  var gadget_klass = rJS(window),
    alert_message_content = gadget_klass.__template_element
                         .getElementById("alert-message-template")
                         .innerHTML,
    alert_message_template = Handlebars.compile(alert_message_content);

  gadget_klass
    .declareAcquiredMethod("getUrlFor", "getUrlFor")

    .declareMethod("render", function (options) {
      var gadget = this,
        // html_message,
        message_content = domsugar('div'),
        // closable = options.can_close || false,
        id = "alert"  + new Date().getTime();

      message_content.id = id;
      message_content.setAttribute("data-key", options.key || "");
      return new RSVP.Queue()
        .push(function () {
          if (options.value.link) {
            return gadget.getUrlFor({command: "index",
                                options: {jio_key: options.value.link,
                                          page: "slap_controller"}
            ]);
          return 
        })
        .push(function (result) {
          var element = result[0],
              link = result[1];
          element.innerHTML = alert_message_template({
            link: link,
            message: options.value.text_content,
            title: options.value.title || "",
            type: options.type || "danger"
          });
          return element;
        });
    });
}(document, window, rJS, RSVP, Handlebars));