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

  function checkInstanceStatus(options) {
    if ((!options) || (options && !options.news)) {
      return 'ui-btn-no-data';
    }
    if (options.news.text.startsWith("#access")) {
      return 'ui-btn-ok';
    } else {
      if (options.news.no_data) {
        return 'ui-btn-no-data';
      }
      else if (options.news.is_slave) {
        return 'ui-btn-is-slave';
      }
      else if (options.news.is_stopped) {
        return 'ui-btn-is-stopped';
      }
      else if (options.news.is_destroyed) {
        return 'ui-btn-is-destroyed';
      }
      return 'ui-btn-error';
    }
  }

  function getStatus(gadget, result) {
    var status_class = 'ui-btn-no-data',
        status_title = 'Instance',
        status_style = "",
        monitor_url,
        template = inline_status_template;

    monitor_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type%3A%22Software%20Instance%22%20AND%20reference%3A%22' + result.reference + '%22';
    status_class = checkInstanceStatus(result);
    if (status_class === 'ui-btn-is-slave') {
      status_class = 'ui-btn-no-data';
      status_style = "color: white !important;";
      status_title = 'Slave';
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
    .ready(function (gadget) {
      gadget.props = {};
      return gadget.getSetting("hateoas_url")
        .push(function (url) {
          gadget.props.hateoas_url = url;
        });
    })
    .declareAcquiredMethod("jio_get", "jio_get")
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