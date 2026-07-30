(function () {
  "use strict";

  var messageElement = document.getElementById("message");
  var allServices = [];
  var currentView = "cells";

  //////////////////////////////////////////////////////
  // JSON-RPC helper
  //////////////////////////////////////////////////////

  function callJsonRpc(method, data) {
    // relative path so this works standalone or behind a reverse proxy
    // adding a path prefix (this page lives at .../henri/, the json-rpc
    // API lives one level up, at the root of the slapproxy application)
    return fetch("../" + method, {
      method: "POST",
      headers: {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data || {})
    }).then(function (response) {
      if (!response.ok) {
        return response.json().then(function (error) {
          throw new Error(error.title || response.statusText);
        });
      }
      return response.json();
    });
  }

  function showError(error) {
    messageElement.textContent = "Error: " + error.message;
  }

  //////////////////////////////////////////////////////
  // "_"-wrapped JSON convention helpers
  //
  // Some software releases store all parameters as a single JSON string
  // under a "_" key; others publish flat keys directly. Both appear in
  // this same proxy.
  //////////////////////////////////////////////////////

  function isWrapped(dict) {
    var keys = Object.keys(dict || {});
    return keys.length === 1 && keys[0] === "_";
  }

  function unwrapParameters(dict) {
    if (isWrapped(dict)) {
      try {
        return JSON.parse(dict["_"]);
      } catch (error) {
        return dict;
      }
    }
    return dict || {};
  }

  // Re-wrap edited parameters the same way the original ones were shaped,
  // so software releases expecting the "_" convention keep working.
  function rewrapParameters(originalRaw, editedUnwrapped) {
    if (isWrapped(originalRaw)) {
      return {"_": JSON.stringify(editedUnwrapped)};
    }
    return editedUnwrapped;
  }

  //////////////////////////////////////////////////////
  // Loading services
  //////////////////////////////////////////////////////

  function loadAllServices() {
    return callJsonRpc("slapos.allDocs.v0.instance_tree_list", {})
      .then(function (result) {
        return Promise.all(result.result_list.map(function (item) {
          return callJsonRpc("slapos.get.v0.instance_tree", {
            title: item.title
          });
        }));
      })
      .then(function (serviceList) {
        allServices = serviceList;
        messageElement.textContent = "";
        renderCurrentView();
      }, showError);
  }

  function findCoreNetworkApnList() {
    var apnList = [];
    allServices.forEach(function (service) {
      if (service.software_type !== "core-network" || service.shared) {
        return;
      }
      var parameters = unwrapParameters(service.parameters);
      ["pdn1", "pdn2"].forEach(function (pdnKey) {
        var pdn = parameters[pdnKey];
        if (pdn && pdn.apn_list) {
          apnList = apnList.concat(pdn.apn_list);
        }
      });
    });
    return apnList;
  }

  //////////////////////////////////////////////////////
  // View switching
  //////////////////////////////////////////////////////

  var CELL_SOFTWARE_TYPE_LIST = ["enb", "gnb", "enb-gnb"];

  function renderCurrentView() {
    if (currentView === "cells") {
      renderRootServiceListView(CELL_SOFTWARE_TYPE_LIST, document.getElementById("cells-list"));
    } else if (currentView === "core-network") {
      renderRootServiceListView(["core-network"], document.getElementById("core-network-list"));
    } else if (currentView === "sim-management") {
      renderSimManagement();
    }
  }

  function setActiveView(view) {
    currentView = view;
    document.querySelectorAll(".nav-item").forEach(function (button) {
      button.classList.toggle("active", button.dataset.view === view);
    });
    document.querySelectorAll(".view").forEach(function (section) {
      section.classList.toggle("active", section.id === "view-" + view);
    });
    renderCurrentView();
  }

  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.addEventListener("click", function () {
      setActiveView(button.dataset.view);
    });
  });

  //////////////////////////////////////////////////////
  // Connection parameter grouping (by dotted prefix, e.g. "CELL.foo")
  //////////////////////////////////////////////////////

  function groupConnectionParameters(dict) {
    var groups = {};
    Object.keys(dict).sort().forEach(function (key) {
      var dotIndex = key.indexOf(".");
      var groupName = dotIndex === -1 ? "General" : key.slice(0, dotIndex);
      var label = dotIndex === -1 ? key : key.slice(dotIndex + 1);
      label = label.replace(/-/g, " ");
      if (!groups[groupName]) {
        groups[groupName] = [];
      }
      groups[groupName].push({label: label, value: dict[key]});
    });
    return groups;
  }

  function renderConnectionParameters(container, connectionParameters) {
    var flat = unwrapParameters(connectionParameters);
    var groups = groupConnectionParameters(flat);
    var groupNames = Object.keys(groups).sort();
    if (groupNames.length === 0) {
      container.appendChild(document.createElement("p")).textContent =
        "No connection parameters.";
      return;
    }
    groupNames.forEach(function (groupName) {
      var groupDiv = document.createElement("div");
      groupDiv.className = "param-group";
      var heading = document.createElement("h4");
      heading.textContent = groupName;
      groupDiv.appendChild(heading);

      var table = document.createElement("table");
      var tbody = document.createElement("tbody");
      groups[groupName].forEach(function (entry) {
        var row = document.createElement("tr");
        var labelCell = document.createElement("td");
        labelCell.textContent = entry.label;
        var valueCell = document.createElement("td");
        valueCell.textContent = entry.value;
        row.appendChild(labelCell);
        row.appendChild(valueCell);
        tbody.appendChild(row);
      });
      table.appendChild(tbody);
      groupDiv.appendChild(table);
      container.appendChild(groupDiv);
    });
  }

  //////////////////////////////////////////////////////
  // Shared root-service detail card (used by Cells and Core Network)
  //////////////////////////////////////////////////////

  function renderRootServiceListView(softwareTypeList, container) {
    container.innerHTML = "";
    var services = allServices.filter(function (service) {
      return softwareTypeList.indexOf(service.software_type) !== -1 && !service.shared;
    });
    if (services.length === 0) {
      container.appendChild(document.createElement("p")).textContent =
        "No services of type \"" + softwareTypeList.join("\", \"") + "\" found.";
      return;
    }
    services.forEach(function (service) {
      container.appendChild(renderServiceDetail(service));
    });
  }

  function renderServiceDetail(service) {
    var card = document.createElement("div");
    card.className = "service-card";

    var header = document.createElement("div");
    header.className = "view-header";
    var title = document.createElement("h2");
    title.textContent = service.title;
    header.appendChild(title);

    var editButton = document.createElement("button");
    editButton.type = "button";
    editButton.className = "edit-button";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", function () {
      openEditServiceModal(service);
    });
    header.appendChild(editButton);
    card.appendChild(header);

    var meta = document.createElement("div");
    meta.className = "service-meta";
    meta.textContent = "State: " + service.state +
      " — Software type: " + service.software_type +
      " — Software release: " + service.software_release_uri;
    card.appendChild(meta);

    var connectionHeading = document.createElement("h3");
    connectionHeading.textContent = "Connection parameters";
    card.appendChild(connectionHeading);
    var connectionContainer = document.createElement("div");
    card.appendChild(connectionContainer);
    renderConnectionParameters(connectionContainer, service.connection_parameters);

    var parametersHeading = document.createElement("h3");
    parametersHeading.textContent = "Parameters";
    card.appendChild(parametersHeading);
    var pre = document.createElement("pre");
    pre.className = "raw-parameters";
    pre.textContent = JSON.stringify(unwrapParameters(service.parameters), null, 2);
    card.appendChild(pre);

    return card;
  }

  function openEditServiceModal(service) {
    var unwrapped = unwrapParameters(service.parameters);
    var body = document.createElement("div");
    var label = document.createElement("label");
    label.textContent = "Parameters (JSON)";
    var textarea = document.createElement("textarea");
    textarea.value = JSON.stringify(unwrapped, null, 2);
    label.appendChild(document.createElement("br"));
    label.appendChild(textarea);
    body.appendChild(label);

    openModal("Edit " + service.title, body, function () {
      var edited;
      try {
        edited = JSON.parse(textarea.value);
      } catch (error) {
        throw new Error("Invalid JSON: " + error.message);
      }
      return callJsonRpc("slapos.post.v0.software_instance", {
        title: service.title,
        software_release_uri: service.software_release_uri,
        software_type: service.software_type,
        shared: service.shared,
        parameters: rewrapParameters(service.parameters, edited),
        sla_parameters: service.sla_parameters,
        // Always pass the current state through explicitly: the API
        // defaults to "started" when state is omitted, which would
        // silently restart a stopped service on every edit.
        state: service.state
      }).then(loadAllServices);
    });
  }

  //////////////////////////////////////////////////////
  // SIM Management
  //////////////////////////////////////////////////////

  function renderSimManagement() {
    var tbody = document.querySelector("#sim-table tbody");
    tbody.innerHTML = "";
    var apnList = findCoreNetworkApnList();
    var apnText = apnList.length > 0 ? apnList.join(", ") : "—";

    var sims = allServices.filter(function (service) {
      return service.shared;
    });

    sims.forEach(function (sim) {
      var connectionParameters = unwrapParameters(sim.connection_parameters);
      var parameters = unwrapParameters(sim.parameters);
      var enabled = !parameters.disable_sim;

      var row = document.createElement("tr");

      var imsiCell = document.createElement("td");
      imsiCell.textContent = connectionParameters.imsi || parameters.imsi || "—";
      row.appendChild(imsiCell);

      var nameCell = document.createElement("td");
      nameCell.textContent = sim.title;
      row.appendChild(nameCell);

      var apnCell = document.createElement("td");
      apnCell.textContent = apnText;
      row.appendChild(apnCell);

      var statusCell = document.createElement("td");
      statusCell.textContent = enabled ? "Enabled" : "Disabled";
      statusCell.className = enabled ? "status-enabled" : "status-disabled";
      row.appendChild(statusCell);

      var actionsCell = document.createElement("td");

      var editButton = document.createElement("button");
      editButton.type = "button";
      editButton.title = "Edit";
      editButton.textContent = "✏️";
      editButton.addEventListener("click", function () {
        openEditSimModal(sim);
      });
      actionsCell.appendChild(editButton);

      var deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.title = "Delete";
      deleteButton.textContent = "🗑️";
      deleteButton.addEventListener("click", function () {
        deleteSim(sim);
      });
      actionsCell.appendChild(deleteButton);

      row.appendChild(actionsCell);
      tbody.appendChild(row);
    });
  }

  function buildReadOnlyField(labelText, value) {
    var label = document.createElement("label");
    label.textContent = labelText;
    var input = document.createElement("input");
    input.type = "text";
    input.value = value || "";
    input.disabled = true;
    label.appendChild(document.createElement("br"));
    label.appendChild(input);
    return label;
  }

  function buildTextField(labelText, value) {
    var label = document.createElement("label");
    label.textContent = labelText;
    var input = document.createElement("input");
    input.type = "text";
    input.value = value || "";
    label.appendChild(document.createElement("br"));
    label.appendChild(input);
    return {label: label, input: input};
  }

  function openEditSimModal(sim) {
    var connectionParameters = unwrapParameters(sim.connection_parameters);
    var parameters = unwrapParameters(sim.parameters);

    var body = document.createElement("div");
    body.appendChild(buildReadOnlyField("IMSI", connectionParameters.imsi || parameters.imsi));
    body.appendChild(buildReadOnlyField("MSIN", parameters.msin));
    body.appendChild(buildReadOnlyField("PLMN", parameters.plmn));

    var simAlgoField = buildTextField("SIM algorithm", parameters.sim_algo);
    body.appendChild(simAlgoField.label);
    var opcField = buildTextField("OPc", parameters.opc);
    body.appendChild(opcField.label);
    var kField = buildTextField("K", parameters.k);
    body.appendChild(kField.label);

    var disableLabel = document.createElement("label");
    var disableCheckbox = document.createElement("input");
    disableCheckbox.type = "checkbox";
    disableCheckbox.checked = !!parameters.disable_sim;
    disableLabel.appendChild(disableCheckbox);
    disableLabel.appendChild(document.createTextNode(" Disable this SIM"));
    body.appendChild(disableLabel);

    openModal("Edit " + sim.title, body, function () {
      var edited = Object.assign({}, parameters, {
        sim_algo: simAlgoField.input.value,
        opc: opcField.input.value,
        k: kField.input.value,
        disable_sim: disableCheckbox.checked
      });
      return callJsonRpc("slapos.post.v0.software_instance", {
        title: sim.title,
        software_release_uri: sim.software_release_uri,
        software_type: sim.software_type,
        shared: true,
        parameters: rewrapParameters(sim.parameters, edited),
        sla_parameters: sim.sla_parameters,
        state: sim.state
      }).then(loadAllServices);
    });
  }

  function deleteSim(sim) {
    if (!window.confirm("Delete SIM \"" + sim.title + "\"?")) {
      return;
    }
    messageElement.textContent = "";
    callJsonRpc("slapos.post.v0.software_instance", {
      title: sim.title,
      software_release_uri: sim.software_release_uri,
      software_type: sim.software_type,
      shared: true,
      parameters: sim.parameters,
      sla_parameters: sim.sla_parameters,
      state: "destroyed"
    }).then(loadAllServices, showError);
  }

  document.getElementById("add-sim-button").addEventListener("click", function () {
    var coreNetwork = allServices.filter(function (service) {
      return service.software_type === "core-network" && !service.shared;
    })[0];
    if (!coreNetwork) {
      showError(new Error("No core-network service found to attach the SIM to."));
      return;
    }

    var body = document.createElement("div");
    var titleField = buildTextField("Device name", "");
    body.appendChild(titleField.label);
    var imsiField = buildTextField("IMSI", "");
    body.appendChild(imsiField.label);
    var msinField = buildTextField("MSIN", "");
    body.appendChild(msinField.label);
    var plmnField = buildTextField("PLMN", "00101");
    body.appendChild(plmnField.label);
    var simAlgoField = buildTextField("SIM algorithm", "milenage");
    body.appendChild(simAlgoField.label);
    var opcField = buildTextField("OPc", "");
    body.appendChild(opcField.label);
    var kField = buildTextField("K", "");
    body.appendChild(kField.label);

    openModal("Add SIM", body, function () {
      if (!titleField.input.value) {
        throw new Error("Device name is required.");
      }
      var parameters = {
        sim_algo: simAlgoField.input.value,
        imsi: imsiField.input.value,
        msin: msinField.input.value,
        plmn: plmnField.input.value,
        opc: opcField.input.value,
        k: kField.input.value
      };
      return callJsonRpc("slapos.post.v0.software_instance", {
        title: titleField.input.value,
        software_release_uri: coreNetwork.software_release_uri,
        software_type: "core-network",
        shared: true,
        parameters: parameters,
        sla_parameters: {},
        state: "started"
      }).then(loadAllServices);
    });
  });

  //////////////////////////////////////////////////////
  // Modal
  //////////////////////////////////////////////////////

  var modalOverlay = document.getElementById("modal-overlay");
  var modalTitle = document.getElementById("modal-title");
  var modalBody = document.getElementById("modal-body");
  var modalSaveHandler = null;

  function openModal(title, bodyNode, onSave) {
    modalTitle.textContent = title;
    modalBody.innerHTML = "";
    modalBody.appendChild(bodyNode);
    modalSaveHandler = onSave;
    modalOverlay.classList.remove("hidden");
  }

  function closeModal() {
    modalOverlay.classList.add("hidden");
    modalSaveHandler = null;
  }

  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("modal-save").addEventListener("click", function () {
    if (!modalSaveHandler) {
      return;
    }
    messageElement.textContent = "";
    try {
      Promise.resolve(modalSaveHandler()).then(closeModal, showError);
    } catch (error) {
      showError(error);
    }
  });

  document.addEventListener("DOMContentLoaded", function () {
    setActiveView("cells");
    loadAllServices();
  });
}());
