/*globals console, window, rJS, RSVP, loopEventListener, i18n, Handlebars, $*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    inline_status_source = gadget_klass.__template_element
                         .getElementById("inline-status-template")
                         .innerHTML,
    inline_status_template = Handlebars.compile(inline_status_source);

  function checkComputeNodeStatus(options) {
    if (!options || !options.news || !options.news.text) {
      return 'ui-btn-no-data';
    }
    if (options.news.text.startsWith("#access")) {
      if (options.news.no_data_since_15_minutes) {
        return 'ui-btn-error';
      }
      if (options.news.no_data_since_5_minutes) {
        return 'ui-btn-warning';
      }
      return 'ui-btn-ok';
    }
    if (options.news.no_data) {
      return 'ui-btn-no-data';
    }
    return 'ui-btn-error';
  }

  function checkComputePartitionStatus(options) {
    var message,
      compute_partition,
      partition_class = 'ui-btn-ok',
      error_amount = 0,
      total_amount = 0;

    if (!options || !options.compute_partition_news) {
      return 'ui-btn-no-data';
    }

    for (compute_partition in options.compute_partition_news) {
      if (options.compute_partition_news.hasOwnProperty(compute_partition) &&
          options.compute_partition_news[compute_partition].text) {
        message = options.compute_partition_news[compute_partition].text;
        if (message.startsWith("#error")) {
          partition_class = 'ui-btn-warning';
          error_amount += 1;
        }
        total_amount += 1;

        if ((error_amount > 0) && (error_amount < total_amount)) {
          // No need to continue the result will be a warnning
          return partition_class;
        }
      }
    }
    if (total_amount === 0) {
      return 'ui-btn-no-data';
    }

    if (error_amount === total_amount) {
      // No need to continue the result will be a warnning
      return 'ui-btn-error';
    }
    return partition_class;
  }

  function getStatus(gadget, result) {
    var monitor_url,
      status_class = 'ui-btn-no-data',
      status_title = 'Compute Node',
      right_title = 'Partitions',
      right_class = 'ui-btn-no-data',
      status_style = '',
      right_style = '';

    if (result && result.news && result.news.compute_node) {
      status_class = checkComputeNodeStatus({news: result.news.compute_node});
    }
    if ((status_class === 'ui-btn-error') ||
          (status_class === 'ui-btn-no-data')) {
      right_class = status_class;
    } else {
      if (result && result.news && result.news.partition) {
        right_class = checkComputePartitionStatus(
          {compute_partition_news: result.news.partition}
        );
      }
    }

    monitor_url = 'https://monitor.app.officejs.com/#/' +
      '?page=ojsm_dispatch&query=portal_type%3A%22Software%20Instance%22%20' +
      'AND%20aggregate_reference%3A%22' + result.reference + '%22';

    gadget.element.innerHTML = inline_status_template({
      monitor_url: monitor_url,
      status_class: status_class,
      status_title: status_title,
      status_style: status_style,
      right_class: right_class,
      right_title: right_title,
      right_style: right_style
    });
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