/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window);

  function getTemplateById(template_id) {
    var template_source = gadget_klass.__template_element
                         .getElementById(template_id)
                         .innerHTML;
    return Handlebars.compile(template_source);

  }
  gadget_klass

    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("translateHtml", "translateHtml")

    .ready(function (gadget) {
      gadget.props = {};
      return gadget.getSetting("hateoas_url")
        .push(function (url) {
          gadget.props.hateoas_url = url;
        })
        .push(function () {
          gadget.render({});
        });
    })

    .declareMethod("getContent", function () {
      return {};
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        annotated_message = "",
        annotated_message_template,
        annotated_template_id;
        
      gadget.options = options;
      if (options.template_id === undefined) {
        // Verify if template-id is present on the div element
        annotated_template_id = gadget.element.getAttribute("data-template-id");
        annotated_message_template = getTemplateById(annotated_template_id);
        annotated_message = annotated_message_template({});
      } else if (options.template_id !== undefined) {
        annotated_message_template = getTemplateById(options.template_id);
        annotated_message = annotated_message_template({});
      }
      return gadget.getElement()
        .push(function (element) {
          var div = element.querySelector('div.annotated_help');
          div.innerHTML = annotated_message;
          return element;
        });
    });
}(window, rJS, RSVP, Handlebars));