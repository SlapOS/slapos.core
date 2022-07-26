/*globals console, window, rJS, RSVP,  domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, domsugar) {
  "use strict";
  rJS(window)
    .declareAcquiredMethod("getSetting", "getSetting")

    .declareMethod("getContent", function () {
      return {};
    })
    .onStateChange(function () {
      var gadget = this,
        header_text = "By " + gadget.state.author +
           " on " + gadget.state.modification_date + ":",
        header = domsugar("div", {
          class: "slapos-event-discussion-message-header"
        }, [
          domsugar('p', {text: header_text})
        ]);
      if (gadget.state.content_type === 'text/html') {
        return domsugar(gadget.element, {}, [
          header,
          domsugar('div', {
            class: "slapos-event-discussion-message-body",
            text: gadget.state.text_content
          })
        ]);
      }
      return domsugar(gadget.element, {}, [
        header,
        domsugar('div', {
          class: "slapos-event-discussion-message-body"
        }, [
          domsugar("pre", {text: gadget.state.text_content})
        ])
      ]);
    })
    .declareMethod("render", function (options) {
      var gadget = this;
      return gadget.changeState({
        author: options.value.doc.source,
        modification_date: options.value.doc.modification_date,
        text_content: options.value.doc.text_content,
        content_type: options.value.doc.content_type
      });
    });
}(window, rJS, domsugar));