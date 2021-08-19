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
    if (!options) {
      return 'ui-btn-no-data';
    }
    if (options.text.startsWith("#access")) {
      if (options.no_data_since_15_minutes) {
        return 'ui-btn-error';
      }
      if (options.no_data_since_5_minutes) {
        return 'ui-btn-warning';
      }
      return 'ui-btn-ok';

    } else {
      if (options.no_data) {
        return 'ui-btn-no-data';
      }
      return 'ui-btn-error';
    }
  }

  function checkComputePartitionStatus(options) {
    var message,
        compute_partition,
        partition_class = 'ui-btn-ok',
        error_amount = 0,
        total_amount = 0;

    if (!options) {
      return 'ui-btn-no-data';
    }

    for (compute_partition in options) {
      message = options[compute_partition].text;
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
    if (!total_amount) {
      return 'ui-btn-no-data';
    }

    if (error_amount === total_amount) {
      return 'ui-btn-error';
    }
    return partition_class;
  }

  function checkNetworkStatus(options) {
    var previous_status = "START",
        status = 'ui-btn-no-data',
        i;
    for (i in options.news.compute_node) {
      status = checkComputeNodeStatus(options.news.compute_node[i]);
      if (previous_status === "START") {
        previous_status = status;
      }
      if (previous_status !== status) {
        if ((previous_status === 'ui-btn-error') && (status === 'ui-btn-ok')) {
          return 'ui-btn-warning';
        }
        if ((status === 'ui-btn-error') && (previous_status === 'ui-btn-ok')) {
          return 'ui-btn-warning';
        }
        if (status === 'ui-btn-no-data') {
          status = previous_status;
        }
      }
    }
    return status;
  }

  function checkNetworkPartitionStatus(options) {
    var compute_node_reference,
        status = 'ui-btn-no-data',
        previous_status = "START";
    for (compute_node_reference in options.news.partition) {
      status = checkComputePartitionStatus(
        options.news.partition[compute_node_reference]);
      if (previous_status === "START") {
        previous_status = status;
      }
      if (status === 'ui-btn-warning') {
        // If status is warning, nothing after will change it.
        return status;
      }
      if (previous_status !== status) {
        if ((previous_status === 'ui-btn-error') && (status === 'ui-btn-ok')) {
          return 'ui-btn-warning';
        }
        if ((status === 'ui-btn-error') && (previous_status === 'ui-btn-ok')) {
          return 'ui-btn-warning';
        }
        if (status === 'ui-btn-no-data') {
          status = previous_status;
        }
      }
    }
    return status;
  }

  function getStatus(gadget, result) {
    var status_class = 'ui-btn-no-data',
      status_title = 'Compute Node',
      right_title = 'Partitions',
      right_class = 'ui-btn-no-data';

    status_class = checkNetworkStatus(result);
    if ((status_class === 'ui-btn-error') ||
          (status_class === 'ui-btn-no-data')) {
      right_class = status_class;
    } else {
      right_class = checkNetworkPartitionStatus(result);
    }

    gadget.element.innerHTML = inline_status_template({
      status_class: status_class,
      status_title: status_title,
      right_class: right_class,
      right_title: right_title
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