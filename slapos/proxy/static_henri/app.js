/* HENRI — High Efficiency New Radio Interface
 *
 * Vendor-neutral 4G/5G ops console on top of slapproxy's JSON-RPC v0 API.
 * Plain ES5, no framework, no build step, no backend change: this file is
 * served straight from static_henri/ by the henri blueprint.
 *
 * Everything shown here is read from the proxy. Where the mockup showed a
 * figure the proxy cannot provide (live radio telemetry, event history),
 * the view says so rather than inventing a number — an ops console that
 * shows a plausible-looking throughput nobody measured is worse than one
 * that shows a dash.
 */
(function () {
  "use strict";

  var messageElement = document.getElementById("message");
  var allServices = [];
  var currentView = "dashboard";
  var eventModeOn = false;
  var lastLoadOk = false;

  var CELL_SOFTWARE_TYPE_LIST = ["enb", "gnb", "enb-gnb"];
  var POSITION_STORAGE_KEY = "henri.production-set.positions";

  var VIEW_TITLES = {
    "dashboard": "Dashboard",
    "ue-monitoring": "UE Monitoring",
    "production-set": "Production Set",
    "cells": "Cells",
    "core-network": "Core Network",
    "sim-management": "SIM Management",
    "events": "Events",
    "settings": "Settings"
  };

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
        renderAllViews();
      }, showError);
  }

  //////////////////////////////////////////////////////
  // View switching
  //////////////////////////////////////////////////////

  function setActiveView(view) {
    if (!VIEW_TITLES[view]) {
      view = "dashboard";
    }
    currentView = view;
    document.querySelectorAll(".nav-item").forEach(function (button) {
      button.classList.toggle("active", button.dataset.view === view);
    });
    document.querySelectorAll(".view").forEach(function (section) {
      section.classList.toggle("active", section.id === "view-" + view);
    });
    element("crumb").textContent = VIEW_TITLES[view];
    element("scroll").scrollTop = 0;
    // keep the view in the URL so a reload comes back to the same page
    if (viewFromHash() !== view) {
      window.location.hash = "#/" + view;
    }
  }

  function viewFromHash() {
    return String(window.location.hash || "").replace(/^#\/?/, "");
  }

  window.addEventListener("hashchange", function () {
    var view = viewFromHash();
    if (view && view !== currentView) {
      setActiveView(view);
    }
  });

  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.addEventListener("click", function () {
      setActiveView(button.dataset.view);
    });
  });

  element("collapse").addEventListener("click", function () {
    element("app").classList.toggle("collapsed");
  });

  element("refresh").addEventListener("click", function () {
    loadAllServices();
  });

  function renderAllViews() {
    renderDashboard();
    renderUeMonitoring();
    renderProductionSet();
    renderCells();
    renderCoreNetwork();
    renderSimManagement();
    renderEvents();
    renderSettings();
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

  //////////////////////////////////////////////////////
  // Dashboard
  //////////////////////////////////////////////////////

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

  function renderDashboard() {
    var cells = cellList();
    var cores = coreNetworkList();
    var sims = simList();
    var groups = deviceGroupList();
    var coreUp = cores.length > 0;
    var enabledSims = sims.filter(function (sim) {
      return !unwrapParameters(sim.parameters).disable_sim;
    });

    element("dash-status").innerHTML =
      statusCard(coreUp && cells.length ? "green" : "amber", ICON.shield, "Network health",
        coreUp && cells.length ? "Ready" : (coreUp ? "No cell" : "No core"),
        "Core and cells as reported by the proxy.") +
      statusCard("blue", ICON.users, "Devices (SIM)",
        enabledSims.length + " of " + sims.length + " enabled",
        "SIM profiles provisioned on this network.") +
      statusCard("violet", ICON.radio, "Radio coverage",
        cells.length + (cells.length === 1 ? " cell" : " cells"),
        "Radio areas devices attach to.") +
      statusCard("green", ICON.core, "Network code", networkCode(),
        "PLMN broadcast by the network.");

    element("dash-identity").innerHTML =
      infoRow("Network name", cores.length ? cores[0].title : "—") +
      infoRow("Network code", networkCode()) +
      dotRow("Core status", coreUp ? "green" : "amber", coreUp ? "Up" : "Absent") +
      dotRow("Base station", cells.length ? "green" : "amber", cells.length ? "Connected" : "None") +
      infoRow("Device groups", groups.length);

    element("dash-groups").innerHTML = groups.length ? groups.map(function (group) {
      var meta = group.meta.map(function (entry) {
        return '<span>' + esc(String(entry.label).toUpperCase()) + ' <b>' + esc(entry.value) + '</b></span>';
      }).join("");
      return '<div class="grp"><div class="grp-n">' + esc(group.name) + '</div>' +
        '<div class="grp-m"><span>FROM <b>' + esc(group.source) + '</b></span>' + meta + '</div></div>';
    }).join("") : '<div class="empty">No device group.<br>Add an APN to a PDN on the core network.</div>';

    element("dash-cells").innerHTML = cells.length ? cells.map(function (cell) {
      return '<div class="grp"><div class="grp-row">' +
        '<div><div class="grp-n">' + esc(cell.title) + '</div>' +
        '<div class="grp-m"><span>' + esc(cellSummary(cell)) + '</span></div></div>' +
        stateBadge(cell.state) + '</div></div>';
    }).join("") : '<div class="empty">No cell configured.</div>';
  }

  function cellSummary(cell) {
    var band = connectionParameter(cell, "RADIO.band");
    var frequency = connectionParameter(cell, "RADIO.dl-frequency");
    var bandwidth = connectionParameter(cell, "RADIO.bandwidth");
    var parts = [];
    if (band) { parts.push(band); }
    if (frequency) { parts.push(frequency + " MHz"); }
    if (bandwidth) { parts.push(bandwidth + " MHz wide"); }
    return parts.length ? parts.join(" · ") : "no radio parameters published";
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

  //////////////////////////////////////////////////////
  // UE Monitoring
  //
  // Live per-UE telemetry (the radio's fast plane) is not part of this
  // console: slapproxy only carries the slow plane, so what we can
  // honestly show is the provisioned fleet and its configuration — never
  // a live throughput or signal level. Radio metrics read a dash rather
  // than showing a made-up figure.
  //////////////////////////////////////////////////////

  var TELEMETRY_DASH = "—";

  function renderUeMonitoring() {
    var sims = simList();
    var enabled = sims.filter(function (sim) {
      return !unwrapParameters(sim.parameters).disable_sim;
    });
    var disabled = sims.length - enabled.length;

    element("ue-status").innerHTML =
      statusCard("blue", ICON.device, "Devices provisioned", sims.length + " SIM",
        "SIM profiles known to the core network.") +
      statusCard("green", ICON.users, "Enabled", enabled.length + " of " + sims.length,
        disabled ? disabled + " SIM disabled in configuration." : "No SIM disabled.") +
      statusCard("grey", ICON.signal, "Signal quality", "No telemetry",
        "Not carried by the configuration plane.") +
      statusCard("grey", ICON.chart, "Data activity", "No telemetry",
        "Not carried by the configuration plane.");

    element("ue-note").innerHTML =
      "This console speaks the configuration plane (slapproxy JSON-RPC v0). " +
      "Per-UE signal, throughput, CQI and MCS are radio-side figures it does not " +
      "carry, so the metrics below read " + TELEMETRY_DASH + " rather than showing " +
      "a made-up number.";

    element("ue-grid").innerHTML = sims.length ? sims.map(function (sim) {
      var parameters = unwrapParameters(sim.parameters);
      var connection = unwrapParameters(sim.connection_parameters);
      var isEnabled = !parameters.disable_sim;
      var imsi = connection.imsi || parameters.imsi;
      return '<div class="ue">' +
        '<div class="ue-h"><div>' +
        '<div class="ue-n">' + esc(sim.title) + '</div>' +
        '<div class="ue-id">SIM ' + esc(orDash(imsi)) + '</div></div>' +
        '<span class="badge ' + (isEnabled ? "b-on" : "b-off") + '">' +
        (isEnabled ? "Enabled" : "Disabled") + '</span></div>' +
        '<div class="chips">' +
        '<span class="chip">PLMN ' + esc(orDash(parameters.plmn)) + '</span>' +
        '<span class="chip">' + esc(orDash(parameters.sim_algo)) + '</span>' +
        '</div>' +
        '<div class="ue-m">' +
        metric("Signal", TELEMETRY_DASH, "dBm") +
        metric("Receiving", TELEMETRY_DASH, "Mbps") +
        metric("Sending", TELEMETRY_DASH, "Mbps") +
        metric("Radio quality", TELEMETRY_DASH, "CQI") +
        metric("Radio mode", TELEMETRY_DASH, "MCS") +
        metric("Timing", TELEMETRY_DASH, "µs TA") +
        '</div></div>';
    }).join("") : '<div class="empty">No SIM provisioned.<br>Add one from SIM Management.</div>';

    element("ue-expert").innerHTML = sims.length ?
      '<table class="tbl"><thead><tr><th>Device name</th><th>IMSI</th><th>MSIN</th>' +
      '<th>Network code</th><th>Algorithm</th><th>Status</th></tr></thead><tbody>' +
      sims.map(function (sim) {
        var parameters = unwrapParameters(sim.parameters);
        var connection = unwrapParameters(sim.connection_parameters);
        var isEnabled = !parameters.disable_sim;
        return '<tr><td class="t-name">' + esc(sim.title) + '</td>' +
          '<td class="t-mono">' + esc(orDash(connection.imsi || parameters.imsi)) + '</td>' +
          '<td class="t-mono">' + esc(orDash(parameters.msin)) + '</td>' +
          '<td class="t-mono">' + esc(orDash(parameters.plmn)) + '</td>' +
          '<td class="t-mono">' + esc(orDash(parameters.sim_algo)) + '</td>' +
          '<td><span class="badge ' + (isEnabled ? "b-on" : "b-off") + '">' +
          (isEnabled ? "ENABLED" : "DISABLED") + '</span></td></tr>';
      }).join("") + '</tbody></table>' :
      '<div class="empty">No SIM provisioned.</div>';
  }

  function metric(label, value, unit) {
    return '<div><div class="m-k">' + esc(label) + '</div>' +
      '<div class="m-v">' + esc(value) + '<div class="m-u">' + esc(unit) + '</div></div></div>';
  }

  element("ue-tabs").addEventListener("click", function (event) {
    var tab = event.target.closest(".tab");
    if (!tab) {
      return;
    }
    document.querySelectorAll("#ue-tabs .tab").forEach(function (other) {
      other.classList.toggle("on", other === tab);
    });
    var expert = tab.dataset.tab === "expert";
    element("ue-grid").classList.toggle("hidden", expert);
    element("ue-expert").classList.toggle("hidden", !expert);
  });

  //////////////////////////////////////////////////////
  // Production Set
  //
  // A map of what the proxy knows: cells become hub nodes, *enabled* SIM
  // profiles become device nodes. Disabled SIMs live only in the left-hand
  // list; dragging one onto the canvas writes disable_sim=false through the
  // proxy. Node positions, labels and icons are a pure UI concern — the
  // proxy has no field for them, so they live in localStorage on this
  // browser.
  //////////////////////////////////////////////////////

  var LABEL_STORAGE_KEY = "henri.production-set.labels";

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

  function readLabels() {
    try {
      return JSON.parse(window.localStorage.getItem(LABEL_STORAGE_KEY) || "{}");
    } catch (error) {
      return {};
    }
  }

  function readLabel(title) {
    return readLabels()[title] || {};
  }

  function storeLabel(title, label, icon) {
    var labels = readLabels();
    if (label || icon) {
      labels[title] = {label: label, icon: icon};
    } else {
      delete labels[title];
    }
    try {
      window.localStorage.setItem(LABEL_STORAGE_KEY, JSON.stringify(labels));
    } catch (error) {
      // private browsing, quota, storage disabled: labels just won't persist
    }
  }

  function readPositions() {
    try {
      return JSON.parse(window.localStorage.getItem(POSITION_STORAGE_KEY) || "{}");
    } catch (error) {
      return {};
    }
  }

  function writePositions(positions) {
    try {
      window.localStorage.setItem(POSITION_STORAGE_KEY, JSON.stringify(positions));
    } catch (error) {
      // private browsing, quota, storage disabled: layout just won't persist
    }
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

    element("dev-b").innerHTML =
      '<div class="dev-n">' + esc(node.name) + '</div>' +
      '<div class="dev-m">' + esc(node.subtitle) + '</div>' +
      (node.hub ? "" : '<div class="dev-live">ON THE SET</div>') +
      '<div style="margin-top:14px">' + rows + '</div>';
    element("dev-f").classList.remove("hidden");
    element("dev-note").classList.remove("hidden");
    element("dev-edit").disabled = false;
    element("dev-disable").classList.toggle("hidden", !!node.hub);
  }

  function devRow(label, value) {
    return '<div class="dev-r"><span>' + esc(label) + '</span><b>' + esc(value) + '</b></div>';
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

  /* enabling / disabling a SIM writes disable_sim through the proxy */
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
    hint.textContent = "The label and icon are display names stored in this browser only — " +
      "the proxy keeps the device name \"" + sim.title + "\" unchanged.";
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

  function renderCells() {
    var container = element("cells-list");
    var cells = cellList();
    if (cells.length === 0) {
      container.innerHTML = '<div class="card"><div class="empty">' +
        'No service of type "' + esc(CELL_SOFTWARE_TYPE_LIST.join('", "')) + '" found.' +
        '</div></div>';
      return;
    }
    container.innerHTML = cells.map(function (cell, index) {
      var connection = unwrapParameters(cell.connection_parameters);
      return '<div class="card">' +
        '<div class="card-head"><div class="card-t">' + esc(cell.title) + '</div>' +
        stateBadge(cell.state) + '</div>' +
        '<div class="f2">' +
        readOnlyField("Band", connection["RADIO.band"]) +
        readOnlyField("Centre frequency", connection["RADIO.dl-frequency"], "MHz") +
        readOnlyField("Channel width", connection["RADIO.bandwidth"], "MHz") +
        readOnlyField("Transmit power", connection["POWER.tx-gain"], "dB gain offset") +
        readOnlyField("gNB / eNB id", connection["ID.gnb-id"] || connection["ID.enb-id"]) +
        readOnlyField("Cell id", connection["ID.cell-id"]) +
        '</div>' +
        '<div class="hint">Software type <b>' + esc(cell.software_type) + '</b> · ' +
        'these values are published by the software release and are read-only here.</div>' +
        '<details class="fold"><summary>All connection parameters</summary>' +
        connectionParametersHtml(cell.connection_parameters) + '</details>' +
        '<details class="fold"><summary>Instance parameters</summary>' +
        '<pre class="raw">' + esc(JSON.stringify(unwrapParameters(cell.parameters), null, 2)) + '</pre>' +
        '</details>' +
        '<div style="display:flex;justify-content:flex-end;margin-top:12px">' +
        '<button type="button" class="btn btn-p" data-edit-cell="' + index + '">Edit parameters</button>' +
        '</div></div>';
    }).join("");

    container.querySelectorAll("[data-edit-cell]").forEach(function (button) {
      button.addEventListener("click", function () {
        openEditServiceModal(cells[Number(button.dataset.editCell)]);
      });
    });
  }

  //////////////////////////////////////////////////////
  // Core Network
  //////////////////////////////////////////////////////

  function renderCoreNetwork() {
    var container = element("core-network-list");
    var cores = coreNetworkList();
    if (cores.length === 0) {
      container.innerHTML = '<div class="card"><div class="empty">' +
        'No service of type "core-network" found.</div></div>';
      return;
    }
    var groups = deviceGroupList();

    container.innerHTML = cores.map(function (core, index) {
      var parameters = unwrapParameters(core.parameters);
      var up = core.state === "started";
      return '<div class="card" style="margin-bottom:14px">' +
        '<div class="card-head"><div class="card-t">Status</div>' + stateBadge(core.state) + '</div>' +
        '<div style="font-size:14px;font-weight:600;color:var(--' + (up ? "green" : "amber") + ')">' +
        '<i class="dot d-' + (up ? "green" : "amber") + '"></i>' +
        esc(up ? "Core up" : "Core " + orDash(core.state)) + '</div></div>' +

        '<div class="card" style="margin-bottom:14px">' +
        '<div class="card-t">Configuration</div>' +
        '<div class="f3">' +
        readOnlyField("Network name", core.title) +
        readOnlyField("Network code", parameters.plmn, "PLMN — MCC + MNC") +
        readOnlyField("Software type", core.software_type) +
        '</div>' +
        '<details class="fold"><summary>Instance parameters</summary>' +
        '<pre class="raw">' + esc(JSON.stringify(parameters, null, 2)) + '</pre></details>' +
        '<details class="fold"><summary>Connection parameters</summary>' +
        connectionParametersHtml(core.connection_parameters) + '</details>' +
        '<div style="display:flex;justify-content:flex-end;margin-top:12px">' +
        '<button type="button" class="btn btn-p" data-edit-core="' + index + '">Edit parameters</button>' +
        '</div></div>' +

        '<div class="card">' +
        '<div class="card-t">Device groups (APNs)</div>' +
        (groups.length ? groups.map(function (group) {
          var meta = group.meta.map(function (entry) {
            return '<span>' + esc(String(entry.label).toUpperCase()) + ' <b>' + esc(entry.value) + '</b></span>';
          }).join("");
          return '<div class="grp"><div class="grp-n">' + esc(group.name) + '</div>' +
            '<div class="grp-m"><span>FROM <b>' + esc(group.source) + '</b></span>' + meta + '</div></div>';
        }).join("") : '<div class="empty">No PDN with an APN list on this core network.</div>') +
        '<div class="hint" style="margin-top:10px">Device groups come from the core network’s ' +
        'pdn1 / pdn2 parameters. Every PDN applies to every SIM — there is no per-SIM APN ' +
        'field in software/simpleran. Edit them through "Edit parameters" above.</div>' +
        '</div>';
    }).join("");

    container.querySelectorAll("[data-edit-core]").forEach(function (button) {
      button.addEventListener("click", function () {
        openEditServiceModal(cores[Number(button.dataset.editCore)]);
      });
    });
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

  //////////////////////////////////////////////////////
  // SIM Management
  //////////////////////////////////////////////////////

  function renderSimManagement() {
    var tbody = document.querySelector("#sim-table tbody");
    var sims = simList();
    var groupText = apnText();

    if (sims.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6"><div class="empty">No SIM provisioned.</div></td></tr>';
      return;
    }

    tbody.innerHTML = sims.map(function (sim, index) {
      var parameters = unwrapParameters(sim.parameters);
      var connection = unwrapParameters(sim.connection_parameters);
      var enabled = !parameters.disable_sim;
      return '<tr>' +
        '<td class="t-name">' + esc(sim.title) + '</td>' +
        '<td class="t-mono">' + esc(orDash(connection.imsi || parameters.imsi)) + '</td>' +
        '<td class="t-mono">' + esc(orDash(parameters.plmn)) + '</td>' +
        '<td class="t-mono">' + esc(groupText) + '</td>' +
        '<td><span class="badge ' + (enabled ? "b-on" : "b-off") + '">' +
        (enabled ? "ENABLED" : "DISABLED") + '</span></td>' +
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
      var routeList = routeEditor.getRouteList();
      if (routeList.length > 0) {
        parameters.route_list = routeList;
      }
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
      row.innerHTML =
        '<div class="imp-file">' + esc(item.name) + '</div>' +
        '<div class="imp-meta">IMSI ' + esc(item.params.imsi) +
        ' · ' + esc(item.params.sim_algo || "milenage") +
        ' · K ' + (item.params.k ? "set" : "—") +
        ' · OPc ' + (item.params.opc ? "set" : "—") +
        (item.params.force_ip ? ' · IP ' + esc(item.params.force_ip) : "") + '</div>';
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
        var chain = Promise.resolve();
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

  //////////////////////////////////////////////////////
  // Events / Settings
  //////////////////////////////////////////////////////

  function renderEvents() {
    element("ev-mode").textContent = eventModeOn ? "Event" : "Lab";
    element("ev-badge").textContent = eventModeOn ? "EVENT MODE" : "LAB MODE";
    element("ev-badge").className = "badge " + (eventModeOn ? "b-warn" : "b-off");
    element("ev-cells").textContent = cellList().length;
    element("ev-sims").textContent = simList().length;
    element("ev-groups").textContent = apnText();
  }

  function renderSettings() {
    var cells = cellList();
    var vendor = "—";
    var linked = false;
    cells.forEach(function (cell) {
      var host = connectionParameter(cell, "AMARISOFT.host-id");
      var version = connectionParameter(cell, "HARDWARE.ors-version");
      if (host || version) {
        linked = true;
        vendor = "Amarisoft ORS" + (version ? " · " + version : "");
      }
    });
    element("set-adapter").textContent = vendor;
    element("set-conf-link").innerHTML = linked ?
      '<i class="dot d-green"></i>Connected' :
      '<i class="dot d-amber"></i>No radio parameters published';
    element("set-mode").textContent = eventModeOn ? "Event" : "Lab";
    element("set-count").textContent = allServices.length;
  }

  element("ebtn").addEventListener("click", function () {
    eventModeOn = !eventModeOn;
    var bar = element("eventbar");
    bar.classList.toggle("off", !eventModeOn);
    bar.querySelector(".eb-tag").textContent = eventModeOn ? "EVENT MODE" : "LAB MODE";
    bar.querySelector(".eb-name").textContent = eventModeOn ?
      "Event running — configuration should be treated as locked" :
      "No event running — configuration unlocked";
    element("ebtn").textContent = eventModeOn ? "Deactivate" : "Activate event";
    element("cv-top-label").textContent = eventModeOn ?
      "EVENT MODE · LIVE" : "LAB MODE · CONFIGURATION";
    renderEvents();
    renderSettings();
  });

  //////////////////////////////////////////////////////
  // Modal
  //////////////////////////////////////////////////////

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

  //////////////////////////////////////////////////////
  // "Live" pill — time since the last successful load
  //////////////////////////////////////////////////////

  var secondsSinceLoad = 0;

  function pad(value) {
    return (value < 10 ? "0" : "") + value;
  }

  function updateLivePill() {
    var pill = element("live-pill");
    pill.classList.toggle("stale", !lastLoadOk);
    element("live-label").textContent = lastLoadOk ? "Live" : "Stale";
  }

  window.setInterval(function () {
    secondsSinceLoad += 1;
    element("clock").textContent =
      pad(Math.floor(secondsSinceLoad / 3600)) + ":" +
      pad(Math.floor(secondsSinceLoad / 60) % 60) + ":" +
      pad(secondsSinceLoad % 60);
  }, 1000);

  //////////////////////////////////////////////////////
  // Boot
  //////////////////////////////////////////////////////

  setActiveView(viewFromHash() || "dashboard");
  updateLivePill();
  loadAllServices();
}());
