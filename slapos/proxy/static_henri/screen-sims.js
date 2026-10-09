"use strict";

function renderSimManagement() {
  var tbody = document.querySelector("#sim-table tbody");
  var sims = simList();
  var groupText = apnText();

  if (sims.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8"><div class="empty">No SIM provisioned.</div></td></tr>';
    return;
  }

  tbody.innerHTML = sims.map(function (sim, index) {
    var parameters = unwrapParameters(sim.parameters);
    var connection = unwrapParameters(sim.connection_parameters);
    var enabled = !parameters.disable_sim;
    return '<tr>' +
      '<td class="t-name">' + esc(sim.title) + simAliasHtml(sim.title) + '</td>' +
      '<td class="t-mono">' + esc(orDash(connection.imsi || parameters.imsi)) + '</td>' +
      '<td class="t-mono">' + esc(orDash(parameters.plmn)) + '</td>' +
      '<td class="t-mono">' + esc(groupText) + '</td>' +
      '<td class="t-mono">' + esc(orDash(assignedSimIp(sim))) + '</td>' +
      '<td><span class="badge ' + (enabled ? "b-on" : "b-off") + '">' +
      (enabled ? "ENABLED" : "DISABLED") + '</span></td>' +
      '<td>' + simRouteBadges(sim) + '</td>' +
      '<td><div class="t-act">' +
      '<button type="button" class="btn" data-edit-sim="' + index + '">Edit</button>' +
      '<button type="button" class="btn" data-delete-sim="' + index + '">Delete</button>' +
      '</div></td></tr>';
  }).join("");

  tbody.querySelectorAll("[data-edit-sim]").forEach(function (button) {
    button.addEventListener("click", function () {
      openEditSimModal(sims[Number(button.dataset.editSim)]);
    });
  });
  tbody.querySelectorAll("[data-delete-sim]").forEach(function (button) {
    button.addEventListener("click", function () {
      deleteSim(sims[Number(button.dataset.deleteSim)]);
    });
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

element("add-sim-button").addEventListener("click", function () {
  var coreNetwork = coreNetworkList()[0];
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
  var plmnField = buildTextField("Network code (PLMN)", networkCode() === "—" ? "" : networkCode());
  body.appendChild(plmnField.label);
  var simAlgoField = buildTextField("SIM algorithm", "milenage");
  body.appendChild(simAlgoField.label);
  var opcField = buildTextField("OPc", "");
  body.appendChild(opcField.label);
  var kField = buildTextField("K", "");
  body.appendChild(kField.label);
  var routeEditor = buildRouteListEditor([]);
  body.appendChild(routeEditor.container);
  var ipField = buildSimIpField(coreNetwork, "", "");
  body.appendChild(ipField.label);

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
      k: kField.input.value,
      force_ip_pdn1: ipField.getAddress()
    };
    var routeList = routeEditor.getRouteList();
    if (routeList.length > 0) {
      parameters.route_list = routeList;
    }
    return ensureCoreFixedIps(coreNetwork).then(function () {
      return callJsonRpc("slapos.post.v0.software_instance", {
        title: titleField.input.value,
        software_release_uri: coreNetwork.software_release_uri,
        software_type: "core-network",
        shared: true,
        parameters: parameters,
        sla_parameters: {},
        state: "started"
      });
    }).then(loadAllServices);
  });
});

//////////////////////////////////////////////////////
// SIM file import — drag a *.xml / *.json onto HENRI
//
// The files are SlapOS instance-parameter XML: one <parameter id="_">
// holding the SIM JSON (sim_algo, imsi, opc, k, optional force_ip) — the
// exact shape SIM Management already writes. A dropped file is parsed and
// turned into a SIM through the same create call as "Add SIM".
//////////////////////////////////////////////////////

function parseSimParams(text) {
  var trimmed = String(text).trim();
  if (trimmed.charAt(0) === "{") {
    return unwrapParameters(JSON.parse(trimmed));
  }
  var doc = new DOMParser().parseFromString(trimmed, "application/xml");
  if (doc.getElementsByTagName("parsererror").length) {
    throw new Error("not valid XML or JSON");
  }
  var nodes = doc.getElementsByTagName("parameter");
  if (!nodes.length) {
    throw new Error("no <parameter> element found");
  }
  var params = {};
  var index, id, inner, key;
  for (index = 0; index < nodes.length; index += 1) {
    id = nodes[index].getAttribute("id");
    if (id === "_") {
      inner = JSON.parse(nodes[index].textContent);
      for (key in inner) {
        if (Object.prototype.hasOwnProperty.call(inner, key)) {
          params[key] = inner[key];
        }
      }
    } else if (id) {
      params[id] = nodes[index].textContent;
    }
  }
  return params;
}

function createSimInstance(coreNetwork, title, params) {
  var payload = extend(params, {});
  if (!payload.plmn && networkCode() !== "—") {
    payload.plmn = networkCode();
  }
  return callJsonRpc("slapos.post.v0.software_instance", {
    title: title,
    software_release_uri: coreNetwork.software_release_uri,
    software_type: "core-network",
    shared: true,
    parameters: payload,
    sla_parameters: {},
    state: "started"
  });
}

function importSimFiles(fileList) {
  var files = Array.prototype.slice.call(fileList).filter(function (file) {
    return /\.(xml|json)$/i.test(file.name);
  });
  if (!files.length) {
    showError(new Error("Drop a .xml or .json SIM file."));
    return;
  }
  var coreNetwork = coreNetworkList()[0];
  if (!coreNetwork) {
    showError(new Error("No core-network service to attach the SIM to."));
    return;
  }
  var existingImsi = {};
  simList().forEach(function (sim) {
    var parameters = unwrapParameters(sim.parameters);
    var connection = unwrapParameters(sim.connection_parameters);
    var imsi = connection.imsi || parameters.imsi;
    if (imsi) { existingImsi[String(imsi)] = true; }
  });

  Promise.all(files.map(function (file) {
    return file.text().then(function (text) {
      try {
        var params = parseSimParams(text);
        if (!params.imsi) {
          return {name: file.name, error: "no imsi in file"};
        }
        return {name: file.name, params: params,
          duplicate: !!existingImsi[String(params.imsi)]};
      } catch (error) {
        return {name: file.name, error: error.message};
      }
    }, function (error) {
      return {name: file.name, error: "unreadable: " + error.message};
    });
  })).then(function (items) {
    openImportModal(coreNetwork, items);
  });
}

function openImportModal(coreNetwork, items) {
  var body = document.createElement("div");
  var hint = document.createElement("div");
  hint.className = "modal-hint";
  hint.textContent = "Each valid file becomes a SIM on " + coreNetwork.title +
    ". IMSI, key (K) and OPc come from the file; give each a device name.";
  body.appendChild(hint);

  var rows = [];
  var importTaken = {};
  items.forEach(function (item) {
    var row = document.createElement("div");
    row.className = "imp-row";
    if (item.error || item.duplicate) {
      row.className += " imp-bad";
      row.innerHTML = '<div class="imp-file">' + esc(item.name) + '</div>' +
        '<div class="imp-note">' +
        (item.duplicate ? "IMSI " + esc(item.params.imsi) + " already provisioned — skipped" :
          "cannot import — " + esc(item.error)) + '</div>';
      body.appendChild(row);
      return;
    }
    var defaultTitle = "SIM " + item.params.imsi;
    var planned = "";
    try {
      planned = item.params.force_ip_pdn1 || item.params.force_ip || nextFreeSimIp(coreNetwork, "", importTaken);
      if (item.params.force_ip_pdn1 || item.params.force_ip) {
        assertSimIpAvailable(coreNetwork, planned, "", importTaken);
      }
      importTaken[planned] = true;
      item.params.force_ip_pdn1 = planned;
      delete item.params.force_ip;
    } catch (error) {
      row.className += " imp-bad";
      row.innerHTML = '<div class="imp-file">' + esc(item.name) + '</div>' +
        '<div class="imp-note">' + esc(error.message) + '</div>';
      body.appendChild(row);
      return;
    }
    row.innerHTML =
      '<div class="imp-file">' + esc(item.name) + '</div>' +
      '<div class="imp-meta">IMSI ' + esc(item.params.imsi) +
      ' · ' + esc(item.params.sim_algo || "milenage") +
      ' · K ' + (item.params.k ? "set" : "—") +
      ' · OPc ' + (item.params.opc ? "set" : "—") +
      ' · IP ' + esc(planned) + '</div>';
    var input = document.createElement("input");
    input.type = "text";
    input.value = defaultTitle;
    row.appendChild(input);
    body.appendChild(row);
    rows.push({item: item, input: input});
  });

  if (!rows.length) {
    body.appendChild(document.createTextNode(""));
  }

  openModal("Import SIM" + (items.length > 1 ? " (" + items.length + " files)" : ""),
    body, function () {
      if (!rows.length) {
        throw new Error("Nothing to import — no valid new SIM in the dropped file(s).");
      }
      var chain = ensureCoreFixedIps(coreNetwork);
      rows.forEach(function (entry) {
        var title = entry.input.value.trim() || ("SIM " + entry.item.params.imsi);
        chain = chain.then(function () {
          return createSimInstance(coreNetwork, title, entry.item.params);
        });
      });
      return chain.then(loadAllServices);
    });
}

/* whole-window file drop: show an overlay while a file is dragged over */
var dropDepth = 0;

function dragHasFiles(event) {
  var types = event.dataTransfer && event.dataTransfer.types;
  if (!types) { return false; }
  return Array.prototype.indexOf.call(types, "Files") !== -1;
}

window.addEventListener("dragenter", function (event) {
  if (!dragHasFiles(event)) { return; }
  event.preventDefault();
  dropDepth += 1;
  element("drop-zone").classList.remove("hidden");
});

window.addEventListener("dragover", function (event) {
  if (!dragHasFiles(event)) { return; }
  event.preventDefault();
  event.dataTransfer.dropEffect = "copy";
});

window.addEventListener("dragleave", function (event) {
  if (!dragHasFiles(event)) { return; }
  dropDepth -= 1;
  if (dropDepth <= 0) {
    dropDepth = 0;
    element("drop-zone").classList.add("hidden");
  }
});

window.addEventListener("drop", function (event) {
  if (!dragHasFiles(event)) { return; }
  event.preventDefault();
  dropDepth = 0;
  element("drop-zone").classList.add("hidden");
  messageElement.textContent = "";
  importSimFiles(event.dataTransfer.files);
});

registerScreen({
  id: "sim-management",
  title: "SIM Management",
  render: renderSimManagement,
  enter: loadOsRoutes,
  refresh: loadOsRoutes
});
