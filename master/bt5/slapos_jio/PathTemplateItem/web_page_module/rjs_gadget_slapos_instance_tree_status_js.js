/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    inline_status_source = gadget_klass.__template_element
                         .getElementById("inline-status-template")
                         .innerHTML,
    inline_status_template = Handlebars.compile(inline_status_source),
    inline_status_no_link_source = gadget_klass.__template_element
                         .getElementById("inline-status-no-link-template")
                         .innerHTML,
    inline_status_no_link_template = Handlebars
                         .compile(inline_status_no_link_source);


  function checkInstanceTreeStatus(options) {
    var message,
        instance,
        partition_class = 'ui-btn-ok',
        error_amount = 0,
        total_amount = 0;

    if ((!options) || (options && !options.instance)) {
      return 'ui-btn-no-data';
    }

    if (options.is_slave) {
      return 'ui-btn-is-slave';
    }
    else if (options.is_stopped) {
      return 'ui-btn-is-stopped';
    }
    else if (options.is_destroyed) {
      return 'ui-btn-is-destroyed';
    }

    for (instance in options.instance) {
      message = options.instance[instance].text;
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

  function getStatus(gadget, result) {
    return new RSVP.Queue()
      .push(function () {
        return getDoc(gadget);
      })
      .push(function (jio_doc) {
        var monitor_url,
          connection_key,
          status_class = 'ui-btn-no-data',
          status_title = 'Instances',
          status_style = "";

        result = jio_doc;
        status_class = checkInstanceTreeStatus(result.news);
        // it should verify if the monitor-base-url is ready.
        for (connection_key in result.connection_parameter_list) {
          if (result.connection_parameter_list[connection_key].connection_key === "monitor-setup-url") {
            monitor_url = result.connection_parameter_list[connection_key].connection_value;
          }
        }
        if (monitor_url === "") {
          monitor_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type%3A%22Instance%20Tree%22%20AND%20title%3A' + result.title;
        }

        if (status_class === 'ui-btn-is-slave') {
          status_class = 'ui-btn-no-data';
          status_style = "color: white !important;";
          status_title = 'Slave Only';
        }
        else if (status_class === 'ui-btn-is-stopped') {
          status_class = 'ui-btn-no-data';
          status_style = "color: white !important;";
          status_title = 'Stopped';
        }
        else if (status_class === 'ui-btn-is-destroyed') {
          status_class = 'ui-btn-no-data';
          status_style = "color: white !important;";
          status_title = 'Destroyed';
        }

        if (status_class === 'ui-btn-no-data') {
          gadget.element.innerHTML = inline_status_no_link_template({
            status_class: status_class,
            status_title: status_title,
            status_style: status_style
          });
        } else {
          gadget.element.innerHTML = inline_status_template({
            monitor_url: monitor_url,
            status_class: status_class,
            status_title: status_title,
            status_style: status_style
          });
        }
        return gadget;
      }
    );
  }

  function getStatusLoop(gadget) {
    return new RSVP.Queue()
      .push(function () {
        return gadget.jio_get(gadget.options.value.jio_key);
      })
      .push(function (result) {
        return getStatus(gadget, result);
      });
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
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("translateHtml", "translateHtml")

    .declareMethod("getContent", function () {
      return {};
    })
    .declareJob("getStatus", function (result) {
      var gadget = this;
      return getStatus(gadget, {news: result});
    })
    .onLoop(function () {
      var gadget = this;
      return getStatusLoop(gadget);
    }, 300000)

    .declareMethod("render", function (options) {
      var gadget = this;
      gadget.options = options;
      gadget.flag = options.value.jio_key;
      return gadget.getStatus(options.value.result);
    });

}(window, rJS, RSVP, Handlebars));