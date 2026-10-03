"use strict";

//////////////////////////////////////////////////////
// Production Set
//
// A map of what the proxy knows: cells become hub nodes, *enabled* SIM
// profiles become device nodes. Disabled SIMs live only in the left-hand
// list; dragging one onto the canvas writes disable_sim=false through the
// proxy. Node positions, labels and icons are a pure UI concern — the
// proxy has no field for them. They are stored in a JSON file on the
// station (GET/PUT production-set), keyed by "sim:<title>" or "cell:<title>".
//////////////////////////////////////////////////////

var LABEL_STORAGE_KEY = "henri.production-set.labels";
var productionSet = {};

var ICON_CHOICES = [
  {icon: "📹", hint: "Camera"},
  {icon: "🎥", hint: "PTZ camera"},
  {icon: "📷", hint: "Stills"},
  {icon: "🎛️", hint: "Vision mixer"},
  {icon: "🎙️", hint: "Commentary"},
  {icon: "🖥️", hint: "Monitor"},
  {icon: "📋", hint: "Tablet"},
  {icon: "📱", hint: "Phone"},
  {icon: "💻", hint: "Laptop"},
  {icon: "📶", hint: "Gateway"},
  {icon: "🛸", hint: "Drone"},
  {icon: "📦", hint: "Generic"}
];

var selectedNode = null;
var simLibraryList = [];

function readBrowserProductionSet() {
  var merged = {};
  try {
    var labels = JSON.parse(window.localStorage.getItem(LABEL_STORAGE_KEY) || "{}");
    Object.keys(labels).forEach(function (title) {
      var entry = labels[title] || {};
      merged["sim:" + title] = {label: entry.label || "", icon: entry.icon || ""};
    });
  } catch (error) {
    // ignore a broken browser cache
  }
  try {
    var positions = JSON.parse(window.localStorage.getItem(POSITION_STORAGE_KEY) || "{}");
    Object.keys(positions).forEach(function (key) {
      merged[key] = merged[key] || {};
      merged[key].x = positions[key].x;
      merged[key].y = positions[key].y;
    });
  } catch (error) {
    // ignore a broken browser cache
  }
  return merged;
}

function saveProductionSet() {
  return fetch("production-set", {
    method: "PUT",
    headers: {"Accept": "application/json", "Content-Type": "application/json"},
    body: JSON.stringify(productionSet)
  }).then(function (response) {
    if (!response.ok) {
      throw new Error("HTTP " + response.status);
    }
    return response.json();
  }).then(function (data) {
    productionSet = data || {};
  }, function () {
    // keep the in-memory copy if the station file cannot be written
  });
}

function loadProductionSet() {
  return fetch("production-set", {headers: {"Accept": "application/json"}})
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      productionSet = data || {};
      if (!Object.keys(productionSet).length) {
        var migrated = readBrowserProductionSet();
        if (Object.keys(migrated).length) {
          productionSet = migrated;
          return saveProductionSet();
        }
      }
    }, function () {
      productionSet = readBrowserProductionSet();
    })
    .then(function () {
      renderProductionSet();
    });
}

function readLabel(title) {
  return productionSet["sim:" + title] || {};
}

function storeLabel(title, label, icon) {
  var key = "sim:" + title;
  var entry = productionSet[key] || {};
  if (label) {
    entry.label = label;
  } else {
    delete entry.label;
  }
  if (icon) {
    entry.icon = icon;
  } else {
    delete entry.icon;
  }
  if (entry.label || entry.icon || typeof entry.x === "number") {
    productionSet[key] = entry;
  } else {
    delete productionSet[key];
  }
  saveProductionSet();
}

function readPositions() {
  var positions = {};
  Object.keys(productionSet).forEach(function (key) {
    var entry = productionSet[key];
    if (entry && typeof entry.x === "number" && typeof entry.y === "number") {
      positions[key] = {x: entry.x, y: entry.y};
    }
  });
  return positions;
}

function writePositions(positions) {
  Object.keys(productionSet).forEach(function (key) {
    if (positions[key]) {
      return;
    }
    var entry = productionSet[key];
    delete entry.x;
    delete entry.y;
    if (!entry.label && !entry.icon) {
      delete productionSet[key];
    }
  });
  Object.keys(positions).forEach(function (key) {
    var entry = productionSet[key] || {};
    entry.x = positions[key].x;
    entry.y = positions[key].y;
    productionSet[key] = entry;
  });
  saveProductionSet();
}

function storePosition(key, x, y) {
  var positions = readPositions();
  positions[key] = {x: x, y: y};
  writePositions(positions);
}

function defaultPosition(index, total, isHub) {
  if (isHub) {
    return {x: 44, y: 44};
  }
  // ring the devices around the hub
  var angle = (2 * Math.PI * index) / Math.max(total, 1) - Math.PI / 2;
  return {
    x: 44 + 34 * Math.cos(angle),
    y: 42 + 32 * Math.sin(angle)
  };
}

function productionNodes() {
  var nodes = [];
  cellList().forEach(function (cell) {
    nodes.push({
      key: "cell:" + cell.title,
      name: cell.title,
      subtitle: (connectionParameter(cell, "RADIO.band") || cell.software_type || "cell").toUpperCase(),
      icon: "📡",
      hub: true,
      service: cell
    });
  });
  simList().forEach(function (sim) {
    var parameters = unwrapParameters(sim.parameters);
    if (parameters.disable_sim) {
      return; // disabled SIMs stay in the left-hand list only
    }
    var connection = unwrapParameters(sim.connection_parameters);
    var meta = readLabel(sim.title);
    nodes.push({
      key: "sim:" + sim.title,
      name: meta.label || sim.title,
      subtitle: String(connection.imsi || parameters.imsi || sim.title),
      icon: meta.icon || iconForName(meta.label || sim.title),
      hub: false,
      enabled: true,
      service: sim
    });
  });
  return nodes;
}

// Labels and device titles are free text ("CAMERA", "Director Tablet"),
// so when no icon was picked explicitly one is guessed from keywords.
var ICON_KEYWORDS = {
  camera: "📹", cam: "📹", studio: "📹", ptz: "🎥",
  stills: "📷", dslr: "📷", photo: "📷",
  mixer: "🎛️", vision: "🎛️", switcher: "🎛️",
  commentary: "🎙️", mic: "🎙️", microphone: "🎙️", intercom: "🎙️", comms: "🎙️",
  monitor: "🖥️", ndi: "🖥️", preview: "🖥️", server: "🖥️",
  tablet: "📋", phone: "📱", laptop: "💻", hub: "💻", drone: "🛸",
  router: "📶", gateway: "📶", relay: "📶", radio: "📡"
};

function iconForName(name) {
  var lowered = " " + String(name || "").toLowerCase() + " ";
  var found = null;
  Object.keys(ICON_KEYWORDS).forEach(function (keyword) {
    if (!found && lowered.indexOf(keyword) !== -1) {
      found = ICON_KEYWORDS[keyword];
    }
  });
  return found || "📦";
}

function renderProductionSet() {
  var canvas = element("canvas");
  var positions = readPositions();
  var nodes = productionNodes();
  var deviceIndex = 0;
  var deviceTotal = nodes.filter(function (node) { return !node.hub; }).length;

  simLibraryList = simList();
  element("sim-lib").innerHTML = simLibraryList.length ? simLibraryList.map(function (sim, index) {
    var parameters = unwrapParameters(sim.parameters);
    var connection = unwrapParameters(sim.connection_parameters);
    var enabled = !parameters.disable_sim;
    var meta = readLabel(sim.title);
    var icon = meta.icon || iconForName(meta.label || sim.title);
    return '<div class="lib-i sim-i" draggable="true" data-sim="' + index + '" title="' +
      (enabled ? "On the set — click to locate it" : "Drag onto the set to enable this SIM") + '">' +
      '<div class="lib-sw" style="background:var(--' + (enabled ? "green" : "red") + ')"></div>' +
      '<div style="font-size:15px">' + icon + '</div>' +
      '<div class="lib-tx"><div class="lib-n">' + esc(meta.label || sim.title) + '</div>' +
      '<div class="lib-d"><i class="dot ' + (enabled ? "d-green" : "d-red") + '"></i>' +
      esc(orDash(connection.imsi || parameters.imsi)) + '</div></div>' +
      '<button type="button" class="tag-btn" data-label-sim="' + index +
      '" title="Set label and icon">&#9998;</button>' +
      '</div>';
  }).join("") : '<div class="empty">No SIM provisioned.<br>Add one from SIM Management.</div>';

  element("cell-lib").innerHTML = cellList().length ? cellList().map(function (cell) {
    var band = connectionParameter(cell, "RADIO.band");
    return '<div class="lib-i cell-i" data-key="cell:' + esc(cell.title) + '" title="Click to locate it">' +
      '<div class="lib-sw" style="background:var(--ink-3)"></div>' +
      '<div style="font-size:15px">📡</div>' +
      '<div class="lib-tx"><div class="lib-n">' + esc(cell.title) + '</div>' +
      '<div class="lib-d">' + esc(String(band || cell.software_type || "cell").toUpperCase()) +
      '</div></div>' + stateBadge(cell.state) + '</div>';
  }).join("") : '<div class="empty">No cell configured.</div>';

  // wipe previously rendered nodes, keep the canvas captions
  canvas.querySelectorAll(".node").forEach(function (node) {
    node.parentNode.removeChild(node);
  });
  selectedNode = null;
  clearDevicePanel();

  nodes.forEach(function (node) {
    var stored = positions[node.key];
    var position = stored || defaultPosition(node.hub ? 0 : deviceIndex, deviceTotal, node.hub);
    if (!node.hub) {
      deviceIndex += 1;
    }
    createNodeElement(node, position.x, position.y);
  });

  element("cv-top-label").textContent = eventModeOn ? "EVENT MODE · LIVE" : "LAB MODE · CONFIGURATION";
  updateCanvasCaption();
}

function updateCanvasCaption() {
  var cells = cellList();
  var deviceCount = element("canvas").querySelectorAll(".node:not(.hub)").length;
  var band = cells.length ? connectionParameter(cells[0], "RADIO.band") : null;
  var bandwidth = cells.length ? connectionParameter(cells[0], "RADIO.bandwidth") : null;
  var parts = ["PRIVATE NETWORK", deviceCount + " OF " + simList().length + " SIM ENABLED"];
  if (band) {
    parts.push(String(band).toUpperCase());
  }
  if (bandwidth) {
    parts.push(bandwidth + " MHZ");
  }
  element("cv-bot").textContent = parts.join(" · ");
}

function createNodeElement(node, x, y) {
  var canvas = element("canvas");
  var el = document.createElement("div");
  el.className = "node" + (node.hub ? " hub" : "");
  el.style.left = x + "%";
  el.style.top = y + "%";
  el.tabIndex = 0;
  el.innerHTML = (node.hub ? '<span class="node-tag">RADIO</span>' : "") +
    '<span class="node-g">' + node.icon + '</span>' +
    '<div class="node-n">' + esc(node.name) + '</div>' +
    '<div class="node-t">' + esc(node.subtitle) + '</div>';
  el._node = node;
  canvas.appendChild(el);
  return el;
}

function clearDevicePanel() {
  element("dev-idx").textContent = "—";
  element("dev-b").innerHTML =
    '<div class="empty">No device selected.<br>Click a node on the canvas.</div>';
  element("dev-f").classList.add("hidden");
  element("dev-note").classList.add("hidden");
  element("dev-disable").classList.add("hidden");
}

function selectNode(el) {
  document.querySelectorAll(".node").forEach(function (other) {
    other.classList.remove("sel");
  });
  el.classList.add("sel");
  selectedNode = el;

  var node = el._node;
  var rows = "";
  var service = node.service;
  var parameters = unwrapParameters(service.parameters);
  var connection = unwrapParameters(service.connection_parameters);

  if (node.hub) {
    element("dev-idx").textContent = "RADIO";
    rows =
      devRow("Software type", orDash(service.software_type)) +
      devRow("State", orDash(service.state)) +
      devRow("Band", orDash(connection["RADIO.band"])) +
      devRow("Centre frequency", connection["RADIO.dl-frequency"] ?
        connection["RADIO.dl-frequency"] + " MHz" : "—") +
      devRow("Channel width", connection["RADIO.bandwidth"] ?
        connection["RADIO.bandwidth"] + " MHz" : "—") +
      devRow("Transmit gain", connection["POWER.tx-gain"] ?
        connection["POWER.tx-gain"] + " dB" : "—") +
      devRow("IP address", orDash(connection["NETWORK.enb-ipv4"]));
  } else {
    element("dev-idx").textContent = "ENABLED";
    rows =
      devRow("Device name", service.title) +
      devRow("IMSI", orDash(connection.imsi || parameters.imsi)) +
      devRow("MSIN", orDash(parameters.msin)) +
      devRow("Network code", orDash(parameters.plmn)) +
      devRow("Algorithm", orDash(parameters.sim_algo)) +
      devRow("Device group", apnText());
  }

  var routeBlock = "";
  if (!node.hub && simDeclaredRoutes(service).length) {
    routeBlock = '<div style="margin-top:14px"><div class="eyebrow" style="margin-bottom:8px">Routes</div>' +
      simRouteBadges(service) + '</div>';
  }

  element("dev-b").innerHTML =
    '<div class="dev-n">' + esc(node.name) + '</div>' +
    '<div class="dev-m">' + esc(node.subtitle) + '</div>' +
    (node.hub ? "" : '<div class="dev-live">ON THE SET</div>') +
    '<div style="margin-top:14px">' + rows + '</div>' +
    routeBlock;
  element("dev-f").classList.remove("hidden");
  element("dev-note").classList.remove("hidden");
  element("dev-edit").disabled = false;
  element("dev-disable").classList.toggle("hidden", !!node.hub);
}
element("dev-edit").addEventListener("click", function () {
  if (!selectedNode || !selectedNode._node.service) {
    return;
  }
  var node = selectedNode._node;
  if (node.hub) {
    openEditServiceModal(node.service);
  } else {
    openEditSimModal(node.service);
  }
});

element("dev-reset").addEventListener("click", function () {
  writePositions({});
  renderProductionSet();
});

/* drag nodes around the canvas — dropping a SIM node on the left list
 * disables it (the reverse of dragging a SIM out of the list) */
var drag = null;
element("canvas").addEventListener("pointerdown", function (event) {
  var el = event.target.closest(".node");
  if (!el) {
    return;
  }
  selectNode(el);
  var canvasRect = element("canvas").getBoundingClientRect();
  var nodeRect = el.getBoundingClientRect();
  drag = {
    el: el,
    offsetX: event.clientX - nodeRect.left,
    offsetY: event.clientY - nodeRect.top,
    rect: canvasRect,
    libRect: element("set-lib").getBoundingClientRect(),
    overLib: false
  };
  el.classList.add("dragging");
  el.setPointerCapture(event.pointerId);
});

element("canvas").addEventListener("pointermove", function (event) {
  if (!drag) {
    return;
  }
  var x = ((event.clientX - drag.offsetX - drag.rect.left) / drag.rect.width) * 100;
  var y = ((event.clientY - drag.offsetY - drag.rect.top) / drag.rect.height) * 100;
  drag.x = Math.max(0, Math.min(88, x));
  drag.y = Math.max(4, Math.min(86, y));
  drag.el.style.left = drag.x + "%";
  drag.el.style.top = drag.y + "%";
  if (drag.el._node && !drag.el._node.hub) {
    drag.overLib = event.clientX >= drag.libRect.left && event.clientX <= drag.libRect.right &&
      event.clientY >= drag.libRect.top && event.clientY <= drag.libRect.bottom;
    element("set-lib").classList.toggle("drop-disable", drag.overLib);
  }
});

function endDrag() {
  if (!drag) {
    return;
  }
  drag.el.classList.remove("dragging");
  element("set-lib").classList.remove("drop-disable");
  if (drag.overLib && drag.el._node && !drag.el._node.hub) {
    setSimEnabled(drag.el._node.service, false);
  } else if (drag.x !== undefined && drag.el._node) {
    storePosition(drag.el._node.key, drag.x, drag.y);
  }
  drag = null;
}

element("canvas").addEventListener("pointerup", endDrag);
element("canvas").addEventListener("pointercancel", function () {
  if (drag) {
    drag.overLib = false; // an aborted drag must never disable the SIM
  }
  endDrag();
});

element("canvas").addEventListener("keydown", function (event) {
  var el = event.target.closest(".node");
  if (!el) {
    return;
  }
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    selectNode(el);
  }
});
element("dev-disable").addEventListener("click", function () {
  if (!selectedNode || !selectedNode._node || selectedNode._node.hub) {
    return;
  }
  setSimEnabled(selectedNode._node.service, false);
});

/* drag a SIM out of the list: dropping it on the canvas enables it */
var draggedSim = null;
element("sim-lib").addEventListener("dragstart", function (event) {
  var item = event.target.closest(".sim-i");
  if (!item) {
    return;
  }
  draggedSim = simLibraryList[Number(item.dataset.sim)];
  event.dataTransfer.effectAllowed = "copy";
});

element("canvas").addEventListener("dragover", function (event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "copy";
});

element("canvas").addEventListener("drop", function (event) {
  event.preventDefault();
  if (!draggedSim) {
    return;
  }
  var sim = draggedSim;
  draggedSim = null;
  var rect = element("canvas").getBoundingClientRect();
  storePosition("sim:" + sim.title,
    Math.max(0, Math.min(88, ((event.clientX - rect.left) / rect.width) * 100 - 6)),
    Math.max(4, Math.min(86, ((event.clientY - rect.top) / rect.height) * 100 - 6)));
  if (unwrapParameters(sim.parameters).disable_sim) {
    setSimEnabled(sim, true);
  } else {
    // already enabled: the drop just repositions its node
    renderProductionSet();
  }
});

/* clicking a list row locates its node; the pencil opens the label modal */
function focusNodeByKey(key) {
  var nodes = element("canvas").querySelectorAll(".node");
  var index;
  for (index = 0; index < nodes.length; index += 1) {
    if (nodes[index]._node && nodes[index]._node.key === key) {
      selectNode(nodes[index]);
      return;
    }
  }
}

element("sim-lib").addEventListener("click", function (event) {
  var labelButton = event.target.closest("[data-label-sim]");
  if (labelButton) {
    openLabelModal(simLibraryList[Number(labelButton.dataset.labelSim)]);
    return;
  }
  var item = event.target.closest(".sim-i");
  if (item) {
    focusNodeByKey("sim:" + simLibraryList[Number(item.dataset.sim)].title);
  }
});

element("cell-lib").addEventListener("click", function (event) {
  var item = event.target.closest(".cell-i");
  if (item) {
    focusNodeByKey(item.dataset.key);
  }
});

function openLabelModal(sim) {
  var meta = readLabel(sim.title);
  var body = document.createElement("div");

  var hint = document.createElement("div");
  hint.className = "modal-hint";
  hint.textContent = "The label and icon are stored on this station. " +
    "The proxy keeps the device name \"" + sim.title + "\" unchanged.";
  body.appendChild(hint);

  var labelField = buildTextField("Label (e.g. CAMERA, MONITOR)", meta.label);
  body.appendChild(labelField.label);

  var iconTitle = document.createElement("label");
  iconTitle.textContent = "Icon";
  body.appendChild(iconTitle);

  var selectedIcon = meta.icon || "";
  var grid = document.createElement("div");
  grid.className = "icon-grid";
  ICON_CHOICES.forEach(function (choice) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = choice.icon;
    button.title = choice.hint;
    button.classList.toggle("on", choice.icon === selectedIcon);
    button.addEventListener("click", function () {
      // clicking the selected icon again clears it back to the guess
      selectedIcon = selectedIcon === choice.icon ? "" : choice.icon;
      grid.querySelectorAll("button").forEach(function (other) {
        other.classList.toggle("on", other.textContent === selectedIcon);
      });
    });
    grid.appendChild(button);
  });
  body.appendChild(grid);

  openModal("Label " + sim.title, body, function () {
    storeLabel(sim.title, labelField.input.value.trim(), selectedIcon);
    renderProductionSet();
  });
}

registerScreen({
  id: "production-set",
  title: "Production Set",
  render: renderProductionSet,
  enter: loadOsRoutes,
  refresh: loadOsRoutes
});
