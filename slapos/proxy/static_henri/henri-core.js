"use strict";

// Shared state and helpers. Each screen file calls registerScreen; an id
// absent from window.HENRI_SCREENS is ignored, so the menu can drop a screen
// without removing the route matching used by SIM badges and Production Set.
function registerScreen(screen) {
  if (!window.HENRI_SCREENS || window.HENRI_SCREENS.indexOf(screen.id) === -1) {
    return;
  }
  window.Henri.screens[screen.id] = screen;
}

var messageElement = document.getElementById("message");
var allServices = [];
var currentView = "dashboard";
var eventModeOn = false;
var lastLoadOk = false;

var CELL_SOFTWARE_TYPE_LIST = ["enb", "gnb", "enb-gnb"];
var POSITION_STORAGE_KEY = "henri.production-set.positions";

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
  lastLoadOk = false;
  updateLivePill();
  messageElement.textContent = "Error: " + error.message;
}

//////////////////////////////////////////////////////
// Small helpers
//////////////////////////////////////////////////////

// Every dynamic value below goes through esc(): titles, IMSIs and
// parameter values come from the database and land in innerHTML.
function esc(value) {
  if (value === undefined || value === null) {
    return "";
  }
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function orDash(value) {
  return (value === undefined || value === null || value === "") ? "—" : value;
}

function extend(target, source) {
  var result = {}, key;
  for (key in target) {
    if (Object.prototype.hasOwnProperty.call(target, key)) {
      result[key] = target[key];
    }
  }
  for (key in source) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      result[key] = source[key];
    }
  }
  return result;
}

function element(id) {
  return document.getElementById(id);
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
// Selectors over the loaded services
//////////////////////////////////////////////////////

function cellList() {
  return allServices.filter(function (service) {
    return CELL_SOFTWARE_TYPE_LIST.indexOf(service.software_type) !== -1 && !service.shared;
  });
}

function coreNetworkList() {
  return allServices.filter(function (service) {
    return service.software_type === "core-network" && !service.shared;
  });
}

function simList() {
  return allServices.filter(function (service) {
    return service.shared;
  });
}

function connectionParameter(service, key) {
  var dict = unwrapParameters(service.connection_parameters);
  return dict[key];
}

// Device groups live on the core-network instance as pdnN objects, each
// carrying an apn_list. Every PDN applies to every SIM — there is no
// per-SIM APN field in software/simpleran/.
function deviceGroupList() {
  var groups = [];
  coreNetworkList().forEach(function (service) {
    var parameters = unwrapParameters(service.parameters);
    Object.keys(parameters).sort().forEach(function (key) {
      if (!/^pdn\d+$/.test(key)) {
        return;
      }
      var pdn = parameters[key];
      if (!pdn || typeof pdn !== "object") {
        return;
      }
      var meta = [];
      Object.keys(pdn).forEach(function (pdnKey) {
        if (pdnKey !== "apn_list" && typeof pdn[pdnKey] !== "object") {
          meta.push({label: pdnKey.replace(/_/g, " "), value: pdn[pdnKey]});
        }
      });
      (pdn.apn_list || []).forEach(function (apn) {
        groups.push({name: apn, source: key, meta: meta});
      });
    });
  });
  return groups;
}

function apnText() {
  var names = deviceGroupList().map(function (group) {
    return group.name;
  });
  return names.length > 0 ? names.join(", ") : "—";
}

//////////////////////////////////////////////////////
// Loading
//////////////////////////////////////////////////////

function loadAllServices() {
  return callJsonRpc("slapos.allDocs.v0.instance_tree_list", {})
    .then(function (result) {
      return Promise.all(result.result_list.map(function (item) {
        return callJsonRpc("slapos.get.v0.instance_tree", {
          title: item.title
        }).then(null, function () {
          // A single unreadable tree (e.g. a half-destroyed shared
          // instance, which the proxy still lists but 500s on) must not
          // blank every view — skip it and render the rest.
          return null;
        });
      }));
    })
    .then(function (serviceList) {
      allServices = serviceList.filter(function (service) {
        return service !== null;
      });
      messageElement.textContent = "";
      lastLoadOk = true;
      secondsSinceLoad = 0;
      updateLivePill();
      if (typeof renderAllViews === "function") {
        renderAllViews();
      }
      if (lastOsPayload && typeof paintOsRoutes === "function") {
        paintOsRoutes(lastOsPayload);
      }
      if (selectedRouteSimTitle && typeof showRouteSim === "function") {
        showRouteSim(selectedRouteSimTitle);
      }
    }, showError);
}
var ROUTE_VALUE_KEYS = {
  via: 1, dev: 1, proto: 1, src: 1, metric: 1, scope: 1, from: 1,
  pref: 1, mtu: 1, weight: 1, table: 1, tos: 1, expires: 1, error: 1,
  advmss: 1, rtt: 1, window: 1, cwnd: 1, ssthresh: 1, realms: 1,
  hoplimit: 1, initcwnd: 1, initrwnd: 1, features: 1, lock: 1, uid: 1
};
var ROUTE_TYPES = {blackhole: 1, unreachable: 1, prohibit: 1, throw: 1};

function parseRouteLine(line) {
  var parts = line.trim().split(/\s+/);
  if (!parts[0]) {
    return null;
  }
  var route = {
    destination: "",
    via: "",
    iface: "",
    source: "",
    proto: "",
    linkdown: false,
    type: ""
  };
  var index = 0;
  if (ROUTE_TYPES[parts[0]]) {
    route.type = parts[0];
    index = 1;
  }
  route.destination = parts[index] || "";
  index += 1;
  while (index < parts.length) {
    var key = parts[index];
    if (key === "linkdown") {
      route.linkdown = true;
      index += 1;
    } else if (key === "onlink") {
      index += 1;
    } else if (ROUTE_VALUE_KEYS[key] && parts[index + 1]) {
      if (key === "via") {
        route.via = parts[index + 1];
      } else if (key === "dev") {
        route.iface = parts[index + 1];
      } else if (key === "src") {
        route.source = parts[index + 1];
      } else if (key === "proto") {
        route.proto = parts[index + 1];
      }
      index += 2;
    } else {
      index += 1;
    }
  }
  return route.destination ? route : null;
}

function parseRouteText(text) {
  return String(text || "").split("\n").map(parseRouteLine).filter(function (route) {
    return route !== null;
  });
}

function splitRouteGroups(routes) {
  var groups = {defaults: [], active: [], rest: []};
  routes.forEach(function (route) {
    if (route.destination === "default") {
      groups.defaults.push(route);
    } else if (!route.linkdown && route.proto !== "babel") {
      groups.active.push(route);
    } else {
      groups.rest.push(route);
    }
  });
  return groups;
}

var lastOsPayload = null;
var kernelRouteByPrefix = null;
var osRoutesError = "";

function ipv4MaskToPrefix(mask) {
  var bits = 0;
  String(mask || "255.255.255.255").split(".").forEach(function (octet) {
    var value = Number(octet);
    var cursor = 128;
    while (cursor > 0) {
      if (value & cursor) {
        bits += 1;
      }
      cursor >>= 1;
    }
  });
  return bits;
}

function ipv4Network(address, prefix) {
  var parts = String(address).split(".").map(Number);
  var ip = ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0;
  var mask = prefix === 0 ? 0 : ((0xffffffff << (32 - prefix)) >>> 0);
  var network = (ip & mask) >>> 0;
  return [
    (network >>> 24) & 255,
    (network >>> 16) & 255,
    (network >>> 8) & 255,
    network & 255
  ].join(".") + "/" + prefix;
}

function expandIpv6(address) {
  var lower = String(address).toLowerCase();
  var halves = lower.split("::");
  if (halves.length > 2) {
    return lower;
  }
  var head = halves[0] ? halves[0].split(":") : [];
  var tail = halves.length === 2 && halves[1] ? halves[1].split(":") : [];
  var groups = head.slice();
  if (halves.length === 2) {
    var missing = 8 - head.length - tail.length;
    while (missing > 0) {
      groups.push("0");
      missing -= 1;
    }
    groups = groups.concat(tail);
  }
  return groups.map(function (group) {
    return group.replace(/^0+/, "") || "0";
  }).join(":");
}

function normalizeCidr(value) {
  if (!value || value === "default") {
    return "";
  }
  var bits = String(value).split("/");
  var address = bits[0];
  var prefix = bits[1];
  if (address.indexOf(":") !== -1) {
    return expandIpv6(address) + "/" + (prefix || "128");
  }
  if (address.indexOf(".") === -1) {
    return "";
  }
  return ipv4Network(address, prefix === undefined ? 32 : Number(prefix));
}

function simDeclaredRoutes(sim) {
  var parameters = unwrapParameters(sim.parameters);
  var list = parameters.route_list;
  if (!list || !list.length) {
    return [];
  }
  return list.map(function (entry) {
    if (!entry) {
      return null;
    }
    if (entry.ipv4_remote_addr) {
      var prefix = entry.mask ? ipv4MaskToPrefix(entry.mask) : 32;
      var cidr = normalizeCidr(entry.ipv4_remote_addr + "/" + prefix);
      return cidr ? {cidr: cidr, label: cidr} : null;
    }
    if (entry.ipv6_remote_addr_prefix) {
      var length = entry.prefix_len === undefined || entry.prefix_len === null ? 128 : entry.prefix_len;
      var v6 = normalizeCidr(entry.ipv6_remote_addr_prefix + "/" + length);
      return v6 ? {cidr: v6, label: v6} : null;
    }
    return null;
  }).filter(function (entry) {
    return entry !== null;
  });
}

function indexKernelRoutes(payload) {
  kernelRouteByPrefix = {};
  ["ipv4", "ipv6"].forEach(function (family) {
    parseRouteText(payload[family]).forEach(function (route) {
      var key = normalizeCidr(route.destination);
      if (!key) {
        return;
      }
      if (!kernelRouteByPrefix[key]) {
        kernelRouteByPrefix[key] = [];
      }
      kernelRouteByPrefix[key].push(route);
    });
  });
}

function simsForPrefix(cidr) {
  if (!cidr) {
    return [];
  }
  return simList().filter(function (sim) {
    return simDeclaredRoutes(sim).some(function (entry) {
      return entry.cidr === cidr;
    });
  });
}

function prefixIsActive(cidr) {
  var installed = kernelRouteByPrefix && kernelRouteByPrefix[cidr];
  if (!installed) {
    return false;
  }
  return installed.some(function (route) {
    return !route.linkdown && !route.type;
  });
}
var selectedRouteSimTitle = null;
function simRouteBadges(sim) {
  var declared = simDeclaredRoutes(sim);
  if (!declared.length) {
    return "—";
  }
  if (osRoutesError) {
    return esc(osRoutesError);
  }
  if (!kernelRouteByPrefix) {
    return "lecture…";
  }
  return declared.map(function (entry) {
    var owners = simsForPrefix(entry.cidr);
    var active = prefixIsActive(entry.cidr);
    var label = owners.length > 1 ? "conflit" : (active ? "active" : "absente");
    var tone = label === "active" ? "b-on" : "b-off";
    return '<div style="margin-bottom:4px">' + esc(entry.label) +
      ' <span class="badge ' + tone + '">' + label + '</span></div>';
  }).join("");
}

function simAliasHtml(title, centered) {
  if (typeof readLabel !== "function") {
    return "";
  }
  var meta = readLabel(title) || {};
  if (!meta.label && !meta.icon) {
    return "";
  }
  return '<div class="sim-alias' + (centered ? " sim-alias-center" : "") + '">' +
    (meta.icon ? '<span class="sim-alias-ico">' + esc(meta.icon) + "</span>" : "") +
    (meta.label ? "<span>" + esc(meta.label) + "</span>" : "") +
    "</div>";
}
function loadOsRoutes() {
  var container = element("routes-body");
  if (currentView === "routes" && container) {
    container.innerHTML = '<div class="card"><div class="empty">Chargement…</div></div>';
  }
  fetch("os-routes", {headers: {"Accept": "application/json"}})
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (payload) {
      lastOsPayload = payload;
      osRoutesError = payload.error || "";
      if (!payload.error) {
        indexKernelRoutes(payload);
      }
      if (typeof paintOsRoutes === "function") {
        paintOsRoutes(payload);
      }
      if (selectedRouteSimTitle && typeof showRouteSim === "function") {
        showRouteSim(selectedRouteSimTitle);
      }
      if (typeof renderSimManagement === "function") {
        renderSimManagement();
      }
      if (typeof selectedNode !== "undefined" && selectedNode && typeof selectNode === "function") {
        selectNode(selectedNode);
      }
    })
    .catch(function (error) {
      osRoutesError = error.message;
      if (container) {
        container.innerHTML = '<div class="card"><div class="empty">' + esc("Routes indisponibles : " + error.message) + "</div></div>";
      }
      if (typeof renderSimManagement === "function") {
        renderSimManagement();
      }
      if (typeof selectedNode !== "undefined" && selectedNode && typeof selectNode === "function") {
        selectNode(selectedNode);
      }
    });
}
//////////////////////////////////////////////////////
// Icons (inline SVG, no icon font to fetch)
//////////////////////////////////////////////////////

var ICON = {
  shield: '<svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
  users: '<svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>',
  radio: '<svg viewBox="0 0 24 24"><line x1="12" y1="20" x2="12" y2="11"/><path d="M7 16a7 7 0 0 1 0-9"/><path d="M17 16a7 7 0 0 0 0-9"/><circle cx="12" cy="8" r="1.6"/></svg>',
  core: '<svg viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></svg>',
  device: '<svg viewBox="0 0 24 24"><rect x="6" y="2" width="12" height="20" rx="2"/><line x1="10" y1="18" x2="14" y2="18"/></svg>',
  signal: '<svg viewBox="0 0 24 24"><path d="M2 9a15 15 0 0 1 20 0"/><path d="M5 13a10 10 0 0 1 14 0"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/></svg>',
  chart: '<svg viewBox="0 0 24 24"><polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/></svg>',
  warn: '<svg viewBox="0 0 24 24"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12" y2="17"/></svg>'
};

function statusCard(tone, icon, eyebrow, value, note) {
  return '<div class="card"><div class="status">' +
    '<div class="st-ico i-' + tone + '">' + icon + '</div>' +
    '<div><div class="eyebrow">' + esc(eyebrow) + '</div>' +
    '<div class="st-val">' + esc(value) + '</div>' +
    '<div class="st-note">' + esc(note) + '</div></div>' +
    '</div></div>';
}

function infoRow(key, value) {
  return '<div class="row"><span class="row-k">' + esc(key) +
    '</span><span class="row-v">' + esc(value) + '</span></div>';
}

function dotRow(key, tone, value) {
  return '<div class="row"><span class="row-k">' + esc(key) +
    '</span><span class="row-v"><i class="dot d-' + tone + '"></i>' + esc(value) + '</span></div>';
}

function networkCode() {
  var cores = coreNetworkList();
  var index;
  for (index = 0; index < cores.length; index += 1) {
    var plmn = unwrapParameters(cores[index].parameters).plmn;
    if (plmn) {
      return plmn;
    }
  }
  var cells = cellList();
  for (index = 0; index < cells.length; index += 1) {
    var broadcast = connectionParameter(cells[index], "CELL.5g-plmn-list") ||
      connectionParameter(cells[index], "CELL.plmn-list");
    if (broadcast) {
      return broadcast;
    }
  }
  return "—";
}
function stateBadge(state) {
  if (state === "started") {
    return '<span class="badge b-on">UP</span>';
  }
  if (state === "destroyed") {
    return '<span class="badge b-warn">DESTROYED</span>';
  }
  return '<span class="badge b-off">' + esc(String(state || "unknown").toUpperCase()) + '</span>';
}
function devRow(label, value) {
  return '<div class="dev-r"><span>' + esc(label) + '</span><b>' + esc(value) + '</b></div>';
}
function setSimEnabled(sim, enabled) {
  var parameters = unwrapParameters(sim.parameters);
  messageElement.textContent = "";
  return callJsonRpc("slapos.post.v0.software_instance", {
    title: sim.title,
    software_release_uri: sim.software_release_uri,
    software_type: sim.software_type,
    shared: true,
    parameters: rewrapParameters(sim.parameters, extend(parameters, {disable_sim: !enabled})),
    sla_parameters: sim.sla_parameters,
    state: sim.state
  }).then(loadAllServices, showError);
}
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

function connectionParametersHtml(connectionParameters) {
  var flat = unwrapParameters(connectionParameters);
  var groups = groupConnectionParameters(flat);
  var groupNames = Object.keys(groups).sort();
  if (groupNames.length === 0) {
    return '<div class="empty">No connection parameter published.</div>';
  }
  return '<div class="params">' + groupNames.map(function (groupName) {
    return '<div class="param-group"><h4>' + esc(groupName) + '</h4>' +
      groups[groupName].map(function (entry) {
        return infoRow(entry.label, entry.value);
      }).join("") + '</div>';
  }).join("") + '</div>';
}

//////////////////////////////////////////////////////
// Cells
//
// Radio values (band, frequency, width, gain) are *connection*
// parameters: the software release publishes them, the GUI cannot write
// them back. They are shown read-only; "Edit parameters" writes the
// instance parameters, which is the actual request path.
//////////////////////////////////////////////////////

function readOnlyField(label, value, hint) {
  return '<div class="field"><label class="lbl">' + esc(label) + '</label>' +
    '<input class="inp" type="text" value="' + esc(orDash(value)) + '" readonly>' +
    (hint ? '<div class="hint">' + esc(hint) + '</div>' : "") + '</div>';
}
function openEditServiceModal(service) {
  var unwrapped = unwrapParameters(service.parameters);
  var body = document.createElement("div");

  var hint = document.createElement("div");
  hint.className = "modal-hint";
  hint.textContent = "Instance parameters are sent back to the proxy as-is. " +
    "The service state (" + service.state + ") is passed through unchanged.";
  body.appendChild(hint);

  var label = document.createElement("label");
  label.textContent = "Parameters (JSON)";
  var textarea = document.createElement("textarea");
  textarea.value = JSON.stringify(unwrapped, null, 2);
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
function buildReadOnlyField(labelText, value) {
  var label = document.createElement("label");
  label.textContent = labelText;
  var input = document.createElement("input");
  input.type = "text";
  input.value = value || "";
  input.disabled = true;
  label.appendChild(input);
  return label;
}

function buildTextField(labelText, value) {
  var label = document.createElement("label");
  label.textContent = labelText;
  var input = document.createElement("input");
  input.type = "text";
  input.value = value || "";
  label.appendChild(input);
  return {label: label, input: input};
}

//////////////////////////////////////////////////////
// Per-SIM IPv4 route editor — the core network routes these remote
// networks through the UE holding the SIM ("route_list" parameter,
// e.g. the LAN behind a 5G gateway).
//////////////////////////////////////////////////////

var IPV4_RE = /^(25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])(\.(25[0-5]|2[0-4][0-9]|1?[0-9]?[0-9])){3}$/;

function buildRouteListEditor(routeList) {
  var container = document.createElement("div");
  container.className = "route-list-editor";
  var heading = document.createElement("label");
  heading.textContent = "IPv4 routes — networks behind this UE";
  container.appendChild(heading);
  var rowContainer = document.createElement("div");
  container.appendChild(rowContainer);

  function addRow(route) {
    var row = document.createElement("div");
    row.className = "route-row";
    var addrInput = document.createElement("input");
    addrInput.type = "text";
    addrInput.placeholder = "Network (e.g. 192.168.13.0)";
    addrInput.value = (route && route.ipv4_remote_addr) || "";
    var maskInput = document.createElement("input");
    maskInput.type = "text";
    maskInput.placeholder = "Mask (e.g. 255.255.255.0)";
    maskInput.value = (route && route.mask) || "";
    var removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "icon-btn";
    removeButton.title = "Remove route";
    removeButton.textContent = "✕";
    removeButton.addEventListener("click", function () {
      rowContainer.removeChild(row);
    });
    row.appendChild(addrInput);
    row.appendChild(maskInput);
    row.appendChild(removeButton);
    rowContainer.appendChild(row);
  }

  (routeList || []).forEach(addRow);

  var addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "btn";
  addButton.textContent = "+ Add route";
  addButton.addEventListener("click", function () {
    addRow();
  });
  container.appendChild(addButton);

  return {
    container: container,
    // Throws on a half-filled or non-IPv4 row so the modal surfaces the
    // error instead of pushing broken routes to the core network.
    getRouteList: function () {
      var editedRouteList = [];
      rowContainer.querySelectorAll(".route-row").forEach(function (row) {
        var inputs = row.querySelectorAll("input");
        var addr = inputs[0].value.trim();
        var mask = inputs[1].value.trim();
        if (!addr && !mask) {
          return;
        }
        if (!IPV4_RE.test(addr) || !IPV4_RE.test(mask)) {
          throw new Error("Invalid route \"" + addr + " / " + mask +
            "\": network and mask must both be dotted IPv4 addresses.");
        }
        editedRouteList.push({ipv4_remote_addr: addr, mask: mask});
      });
      return editedRouteList;
    }
  };
}

function openEditSimModal(sim) {
  var connectionParameters = unwrapParameters(sim.connection_parameters);
  var parameters = unwrapParameters(sim.parameters);

  var body = document.createElement("div");

  var hint = document.createElement("div");
  hint.className = "modal-hint";
  // Renaming a shared instance returns 403 NotImplemented server-side,
  // so the device name is not offered for editing here.
  hint.textContent = "IMSI, MSIN and network code identify the SIM and cannot be changed " +
    "here. The device name is the instance title, which the proxy refuses to rename.";
  body.appendChild(hint);

  body.appendChild(buildReadOnlyField("Device name", sim.title));
  body.appendChild(buildReadOnlyField("IMSI", connectionParameters.imsi || parameters.imsi));
  body.appendChild(buildReadOnlyField("MSIN", parameters.msin));
  body.appendChild(buildReadOnlyField("Network code (PLMN)", parameters.plmn));

  var simAlgoField = buildTextField("SIM algorithm", parameters.sim_algo);
  body.appendChild(simAlgoField.label);
  var opcField = buildTextField("OPc", parameters.opc);
  body.appendChild(opcField.label);
  var kField = buildTextField("K", parameters.k);
  body.appendChild(kField.label);

  var routeEditor = buildRouteListEditor(parameters.route_list);
  body.appendChild(routeEditor.container);

  var disableLabel = document.createElement("label");
  disableLabel.className = "check";
  var disableCheckbox = document.createElement("input");
  disableCheckbox.type = "checkbox";
  disableCheckbox.checked = !!parameters.disable_sim;
  disableLabel.appendChild(disableCheckbox);
  disableLabel.appendChild(document.createTextNode(" Disable this SIM"));
  body.appendChild(disableLabel);

  openModal("Edit " + sim.title, body, function () {
    var edited = extend(parameters, {
      sim_algo: simAlgoField.input.value,
      opc: opcField.input.value,
      k: kField.input.value,
      route_list: routeEditor.getRouteList(),
      disable_sim: disableCheckbox.checked
    });
    if (edited.route_list.length === 0) {
      delete edited.route_list;
    }
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
var modalOverlay = element("modal-overlay");
var modalTitle = element("modal-title");
var modalBody = element("modal-body");
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

element("modal-close").addEventListener("click", closeModal);
element("modal-cancel").addEventListener("click", closeModal);
element("modal-save").addEventListener("click", function () {
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

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape" && !modalOverlay.classList.contains("hidden")) {
    closeModal();
  }
});

var secondsSinceLoad = 0;

function pad(value) {
  return (value < 10 ? "0" : "") + value;
}

function updateLivePill() {
  var pill = element("live-pill");
  pill.classList.toggle("stale", !lastLoadOk);
  element("live-label").textContent = lastLoadOk ? "Live" : "Stale";
}
