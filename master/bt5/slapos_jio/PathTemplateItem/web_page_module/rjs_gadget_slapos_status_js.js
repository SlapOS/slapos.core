/*globals console, window, rJS, i18n, domsugar*/
/*jslint indent: 2, nomen: true, maxlen: 80*/

(function (window, rJS, domsugar) {
  "use strict";
  var gadget_klass = rJS(window);

  function getComputeNodeStatus(options) {
    if (!options || !options.text) {
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
    }
    if (options.no_data) {
      return 'ui-btn-no-data';
    }
    return 'ui-btn-error';
  }

  function getComputePartitionStatus(options) {
    var message,
      compute_partition,
      partition_class = 'ui-btn-ok',
      error_amount = 0,
      total_amount = 0;

    if (!options) {
      return 'ui-btn-no-data';
    }

    for (compute_partition in options) {
      if (options.hasOwnProperty(compute_partition) &&
          options[compute_partition].text) {
        message = options[compute_partition].text;
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
    if (!total_amount) {
      return 'ui-btn-no-data';
    }

    if (error_amount === total_amount) {
      return 'ui-btn-error';
    }
    return partition_class;
  }

  function getComputeNodeStatusList(options) {
    var previous_status = "START",
      status = 'ui-btn-no-data',
      i;
    if (!options || !options.news || !options.news.compute_node) {
      return status;
    }
    for (i in options.news.compute_node) {
      if (options.news.compute_node.hasOwnProperty(i)) {
        status = getComputeNodeStatus(options.news.compute_node[i]);
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
    }
    return status;
  }

  function getComputePartitionStatusList(options) {
    var compute_node_reference,
      status = 'ui-btn-no-data',
      previous_status = "START";
    for (compute_node_reference in options.news.partition) {
      if (options.news.partition.hasOwnProperty(compute_node_reference)) {
        status = getComputePartitionStatus(
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
    }
    return status;
  }

  function getStatus(gadget, result) {
    var status_class = 'ui-btn-no-data',
      right_class = 'ui-btn-no-data',
      computer_node_div = gadget.element.querySelector("compute-node-status"),
      compute_partition_div = gadget.element.querySelector("compute-node-status"),
      monitor_url = '';

    if (result && result.portal_type && result.portal_type === "Compute Node") {
      monitor_url = 'https://monitor.app.officejs.com/#/' +
        '?page=ojsm_dispatch&query=portal_type%3A%22Software%20Instance%22%20' +
        'AND%20aggregate_reference%3A%22' + result.reference + '%22';

      if (result && result.news && result.news.compute_node) {
        status_class = getComputeNodeStatus({news: result.news.compute_node});
      }
      if ((status_class === 'ui-btn-error') ||
            (status_class === 'ui-btn-no-data')) {
        right_class = status_class;
      } else {
        if (result && result.news && result.news.partition) {
          right_class = getComputePartitionStatus(
            {compute_partition_news: result.news.partition}
          );
        }
      }
    } else {
      monitor_url = gadget.options.value.jio_key + '/Base_redirectToMonitor';
      status_class = getComputeNodeStatusList(result);
      if ((status_class === 'ui-btn-error') ||
          (status_class === 'ui-btn-no-data')) {
        right_class = status_class;
      } else {
        right_class = getComputePartitionStatusList(result);
      }
    }

    domsugar(computer_node_div.firstChild,
      {
        class: "ui-bar ui-corner-all first-child " + status_class
      }, [ 
        domsugar("a",
          {
            class: "ui-btn ui-btn-icon-left ui-icon-desktop",
            href: monitor_url,
            target: "_blank",
            // missing translation
            text: 'Compute Node'
          })
      ]);
    domsugar(compute_partition_div.firstChild,
      {
        class: "ui-bar ui-corner-all last-child " + right_class
      }, [
        domsugar("a",
          {
            class: "ui-btn ui-btn-icon-left ui-icon-desktop",
            href: monitor_url,
            target: "_blank",
              // missing translation
            text: 'Partitions'
          })
      ]);
    return gadget;
  }

  gadget_klass
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareMethod("getContent", function () {
      return {};
    })

    .onLoop(function () {
      var gadget = this;
      if (gadget.state.jio_key) {
        return gadget.jio_get(gadget.state.jio_key)
          .push(function (result) {
            return gadget.changeState(result);
          });
      }
    }, 300000)

    .onStateChange(function () {
      return getStatus(this, this.state);
    })

    .declareMethod("render", function (options) {
      var state_dict = options.value.result;
      state_dict.jio_key = options.value.jio_key;
      return this.changeState(state_dict);
    });

}(window, rJS, domsugar));