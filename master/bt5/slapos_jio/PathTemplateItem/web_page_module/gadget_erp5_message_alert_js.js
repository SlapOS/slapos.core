/*globals console, CustomEvent, document, window, rJS, RSVP, Handlebars, loopEventListener*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (CustomEvent, document, window, rJS, RSVP, Handlebars,
           loopEventListener) {
  "use strict";
  var gadget_klass = rJS(window),
    alert_message_content = gadget_klass.__template_element
                         .getElementById("alert-message-template")
                         .innerHTML,
    alert_message_template = Handlebars.compile(alert_message_content);

  function close_click(target, gadget) {
    var master_parent = target.parentElement.parentElement;
    rejectEvent(master_parent);
    if (master_parent.dataset.autoclose === "true") {
      master_parent.remove();
    }
  }

  function reject_click(target, gadget) {
    var master_parent = target.parentElement.parentElement.parentElement;
    rejectEvent(master_parent);
    if (master_parent.dataset.autoclose === "true") {
      master_parent.remove();
    }
  }

  function accept_click(target, gadget) {
    var master_parent = target.parentElement.parentElement.parentElement;
    acceptEvent(master_parent);
    if (master_parent.dataset.autoclose === "true") {
      master_parent.remove();
    }
  }

  function message_click(target, gadget) {
    console.log(target);
  }

  function acceptEvent(target) {
    var accept_event = new CustomEvent('accepted', {
        detail: {
          jio_key: target.dataset.key,
          id: target.id
        },
        bubbles: true,
        cancelable: false
      });
    target.dispatchEvent(accept_event);
  }

  function rejectEvent(target) {
    var reject_event = new CustomEvent('rejected', {
        detail: {
          jio_key: target.dataset.key,
          id: target.id
        },
        bubbles: true,
        cancelable: false
      });
    target.dispatchEvent(reject_event);
  }

  gadget_klass

    .declareMethod("render", function (options) {
      var gadget = this,
          html_message,
          message_content = document.createElement('div'),
          closable = options.can_close || false,
          id = "alert"  + new Date().getTime();

      message_content.id = id;
      message_content.setAttribute("data-key", options.key || "");
      message_content.setAttribute("data-autoclose",
                                   options.auto_close || false);
      html_message = alert_message_template({
        message: options.message,
        title: options.title || "",
        type: options.type || "danger",
        closable: closable,
        question: options.with_question || false
      });
      return gadget.changeState({
        html_message: html_message,
        type: options.type,
        element: message_content,
        gadget_element: options.element || gadget.element
      });
    })
    .onStateChange(function () {
      var gadget = this;
      if (gadget.state.gadget_element.firstChild === null) {
        gadget.state.gadget_element.appendChild(gadget.state.element);
      } else {
        gadget.state.gadget_element.insertBefore(
          gadget.state.element,
          gadget.state.gadget_element.firstChild
        );
      }
      gadget.state.element.innerHTML = gadget.state.html_message;
      return gadget.eventService();
    })

    .declareMethod("closeAlertMessage", function (id) {
      var alert_box;

      if (id.startsWith('alert')) {
        alert_box = document.getElementById(id);
        if (alert_box !== null) {
          return alert_box.remove();
        }
      }
    })

    .declareJob("eventService", function () {
      var gadget = this,
        i,
        close_btn_list = gadget.state.element
          .querySelectorAll('.alert span.close'),
        reject_btn_list = gadget.state.element
          .querySelectorAll('.alert button.alert-btn-reject'),
        accept_btn_list = gadget.state.element
          .querySelectorAll('.alert button.alert-btn-accept'),
        box = gadget.state.element.querySelector('.alert');

      for (i = 0; i < close_btn_list.length; i += 1) {
        loopEventListener(
          close_btn_list[i],
          'click',
          false,
          close_click.bind(gadget, close_btn_list[i], gadget),
          true
        );
      }
      for (i = 0; i < reject_btn_list.length; i += 1) {
        loopEventListener(
          reject_btn_list[i],
          'click',
          false,
          reject_click.bind(gadget, reject_btn_list[i], gadget),
          true
        );
      }
      for (i = 0; i < accept_btn_list.length; i += 1) {
        loopEventListener(
          accept_btn_list[i],
          'click',
          false,
          accept_click.bind(gadget, accept_btn_list[i], gadget),
          true
        );
      }
    });

}(CustomEvent, document, window, rJS, RSVP, Handlebars, loopEventListener));