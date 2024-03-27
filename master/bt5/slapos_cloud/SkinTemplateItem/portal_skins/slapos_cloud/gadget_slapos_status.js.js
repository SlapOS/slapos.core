/*globals console, window, rJS, domsugar */
/*jslint indent: 2, nomen: true, maxlen: 80 */

(function (window, rJS, domsugar) {
  "use strict";
  var gadget_klass = rJS(window);

  function getInstanceStatus(options) {
    if ((!options) || (options && !options.text)) {
      return 'ui-btn-no-data';
    }
    if (options.text.startsWith("#access")) {
      return 'ui-btn-ok';
    }
    if (options.no_data) {
      return 'ui-btn-no-data';
    }
    if (options.is_slave) {
      return 'ui-btn-is-slave';
    }
    if (options.is_stopped) {
      return 'ui-btn-is-stopped';
    }
    if (options.is_destroyed) {
      return 'ui-btn-is-destroyed';
    }
    return 'ui-btn-error';
  }

  function getInstanceTreeStatus(options) {
    var instance;

    if (!options) {
      return 'ui-btn-no-data';
    }

    if (options.is_slave) {
      return 'ui-btn-is-slave';
    }
    if (options.is_stopped) {
      return 'ui-btn-is-stopped';
    }
    if (options.is_destroyed) {
      return 'ui-btn-is-destroyed';
    }

    if (!options.instance) {
      return 'ui-btn-no-data';
    }

    for (instance in options.instance) {
      if (options.instance.hasOwnProperty(instance)) {
        if (options.instance[instance].text.startsWith("#error")) {
          return 'ui-btn-error';
        }
      }
    }
    return 'ui-btn-ok';
  }

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

  function getSoftwareInstallationStatus(options) {
    if ((!options) || (options && !options.text)) {
      return 'ui-btn-no-data';
    }
    if (options.text.startsWith("#access")) {
      return 'ui-btn-ok';
    }
    if (options.text.startsWith("#building")) {
      return 'ui-btn-is-building';
    }
    if (options.no_data) {
      return 'ui-btn-no-data';
    }
    return 'ui-btn-error';
  }


  function getComputeNodeStatusList(options) {
    var previous_status = "START",
      status = 'ui-btn-no-data',
      i;
    if (!options || !options.compute_node) {
      return status;
    }
    for (i in options.compute_node) {
      if (options.compute_node.hasOwnProperty(i)) {
        status = getComputeNodeStatus(options.compute_node[i]);
        if (previous_status === "START") {
          previous_status = status;
        }
        if (previous_status !== status) {
          if ((previous_status === 'ui-btn-error') &&
              (status === 'ui-btn-ok')) {
            // XXX drop warning
            return 'ui-btn-warning';
          }
          if ((status === 'ui-btn-error') &&
              (previous_status === 'ui-btn-ok')) {
            // XXX drop warning
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
      main_status_div = gadget.element.querySelector(".main-status"),
      monitor_url = '',
      main_link_configuration_dict = {
        "class": "ui-btn ui-btn-icon-left ui-icon-desktop"
      };

    if (result && result.monitor_url) {
      monitor_url = result.monitor_url;
    }

    if (result && result.portal_type && result.portal_type === "Compute Node") {
      main_link_configuration_dict.text = 'Node';
      main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      status_class = getComputeNodeStatus(result);
    } else if (result && result.portal_type &&
               result.portal_type === "Software Installation") {
      status_class = getSoftwareInstallationStatus(result);
      main_link_configuration_dict.text = "Installation";
      if (status_class === "ui-btn-is-building") {
        main_link_configuration_dict.text = "Building";
        status_class = "ui-btn-no-data";
      } else if (status_class === "ui-btn-ok") {
        main_link_configuration_dict.text = "Available";
      } else if (status_class === "ui-btn-error") {
        main_link_configuration_dict.text = "Error";
      }
      main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
    } else if (result && result.portal_type && (
        result.portal_type === "Software Instance" ||
        result.portal_type === "Slave Instance"
      )) {
      status_class = getInstanceStatus(result);
      if (status_class === 'ui-btn-is-slave') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Slave';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else if (status_class === 'ui-btn-is-stopped') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Stopped';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else if (status_class === 'ui-btn-is-destroyed') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Destroyed';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else {
        main_link_configuration_dict.href = monitor_url;
        main_link_configuration_dict.target = "_target";
        main_link_configuration_dict.text = 'Instance';
      }
    } else if (result && result.portal_type &&
              result.portal_type === "Instance Tree") {
      status_class = getInstanceTreeStatus(result);
      // it should verify if the monitor-base-url is ready.
      if (status_class === 'ui-btn-is-slave') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Slave Only';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else if (status_class === 'ui-btn-is-stopped') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Stopped';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else if (status_class === 'ui-btn-is-destroyed') {
        status_class = 'ui-btn-color-white';
        main_link_configuration_dict.text = 'Destroyed';
        main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      } else {
        main_link_configuration_dict.href = monitor_url;
        main_link_configuration_dict.target = "_target";
        main_link_configuration_dict.text = 'Instance';
      }
    } else {
      main_link_configuration_dict.text = 'Node';
      main_link_configuration_dict["class"] = "ui-btn ui-btn-icon-left";
      status_class = getComputeNodeStatusList(result);
    }

    main_link_configuration_dict.text = ' ' + main_link_configuration_dict.text;
    domsugar(main_status_div.querySelector('div'),
      {
        "class": "ui-bar ui-corner-all first-child " + status_class
      }, [
        domsugar(main_link_configuration_dict.href ? "a" : "span",
                 main_link_configuration_dict)
      ]);
    return gadget;
  }

  gadget_klass
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareMethod("getContent", function () {
      return {};
    })

    .onStateChange(function () {
      return getStatus(this, this.state);
    })

    .declareMethod("render", function (options) {
      // crash as soon as possible to detect wrong configuration
      if (!(options.hasOwnProperty('jio_key') &&
            options.hasOwnProperty('result'))) {
        throw new Error(
          'status gadget did not receive jio_key  and result values'
        );
      }
      // Save will force the gadget to be updated so
      // result is empty.
      var state_dict = options.result || {};
      state_dict.jio_key = options.jio_key;
      return this.changeState(state_dict);
    });


}(window, rJS, domsugar));