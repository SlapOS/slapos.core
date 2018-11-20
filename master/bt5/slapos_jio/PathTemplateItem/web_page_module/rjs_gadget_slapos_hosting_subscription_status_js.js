/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    inline_status_source = gadget_klass.__template_element
                         .getElementById("inline-status-template")
                         .innerHTML,
    inline_status_template = Handlebars.compile(inline_status_source);

  function checkHostingSubscriptionStatus(options) {
    var message,
        instance,
        partition_class = 'ui-btn-ok',
        error_amount = 0,
        total_amount = 0;

    if ((!options) || (options && !options.news)) {
      return 'ui-btn-no-data';
    }

    for (instance in options.news) {
      message = options.news[instance].text;
      if (message.startsWith("#error")) {
        partition_class = 'ui-btn-warning';
        error_amount++;
      }
      total_amount++;

      if ((error_amount > 0) && (error_amount < total_amount)) {
        // No need to continue the result will be a warnning
        return partition_class;
      }
    }
    if (options.computer_partition === {}) {
      return 'ui-btn-no-data';
    }

    if (error_amount === total_amount) {
      // No need to continue the result will be a warnning
      return 'ui-btn-error';
    }
    return partition_class;
  }

  function getDoc(gadget) {
    if (gadget.options.doc && gadget.options.doc !== undefined) {
      return gadget.options.doc;
    }
    return gadget.jio_get(gadget.options.value.jio_key);
  }

  function getMonitorParameterDict(gadget, doc) {
    if (doc.portal_type === "Hosting Subscription") {
      return gadget.jio_getAttachment(gadget.options.value.jio_key,
        gadget.props.hateoas_url +  gadget.options.value.jio_key +
        "/HostingSubscription_getMonitorParameterDict");
    }
  }

  function getStatus(gadget) {
    var result;
    return new RSVP.Queue()
      .push(function () {
        return getDoc(gadget);
      })
      .push(function (jio_doc) {
        result = jio_doc;
        if (gadget.state.monitor_dict === undefined ||
            !gadget.state.has_monitor_info) {
          return getMonitorParameterDict(gadget, jio_doc)
            .push(function (param_dict) {
              return gadget.changeState({
                monitor_dict: param_dict,
                has_monitor_info: true
              });
            });
        }
      })
      .push(function () {
        var monitor_url,
          status_class = 'ui-btn-no-data',
          status_title = 'Instances',
          status_style = "";

        status_class = checkHostingSubscriptionStatus(result);
        if (gadget.state.monitor_dict.url &&
            gadget.state.monitor_dict.username &&
            gadget.state.monitor_dict.password) {
          monitor_url = "https://monitor.app.officejs.com/f5ce5b1fdc/#page=settings_configurator&url=" +
            gadget.state.monitor_dict.url + "&username=" +
            gadget.state.monitor_dict.username + "&password=" +
            gadget.state.monitor_dict.password;
        } else {
          monitor_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type%3A%22Hosting%20Subscription%22%20AND%20title%3A' + result.title;
        }

        if (status_class === 'ui-btn-no-data') {
          status_style = "color: transparent !important;";
        }
        gadget.element.innerHTML = inline_status_template({
          monitor_url: monitor_url,
          status_class: status_class,
          status_title: status_title,
          status_style: status_style
        });
        return gadget;
      }
    );
  }

  gadget_klass
    .setState({
      has_monitor_info: false
    })
    .ready(function (gadget) {
      gadget.props = {};
      return gadget.getSetting("hateoas_url")
        .push(function (url) {
          gadget.props.hateoas_url = url;
        });
    })
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translateHtml", "translateHtml")

    .declareMethod("getContent", function () {
      return {};
    })
    .declareJob("getStatus", function () {
      var gadget = this;
      return getStatus(gadget);
    })
    .onLoop(function () {
      var gadget = this;
      return getStatus(gadget);
    }, 300000)

    .declareMethod("render", function (options) {
      var gadget = this;
      gadget.options = options;
      gadget.flag = options.value.jio_key;
      return gadget.getStatus();
    });
}(window, rJS, RSVP, Handlebars));