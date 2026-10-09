"use strict";

//////////////////////////////////////////////////////
// UE Monitoring
//
// Configuration still comes from slapproxy. Live figures come from
// GET radio-stats, which polls the Amarisoft gNB and core on this
// station. The throughput curve is kept in this page only.
//////////////////////////////////////////////////////

var TELEMETRY_DASH = "—";
var lastRadio = null;
var radioError = "";
var radioTimer = null;
var radioHistory = [];
var attachBaseline = null;

function startRadioPoll() {
  loadRadioStats();
  if (radioTimer) {
    return;
  }
  radioTimer = setInterval(function () {
    if (currentView === "ue-monitoring") {
      loadRadioStats();
    }
  }, 2500);
}

function stopRadioPoll() {
  if (radioTimer) {
    clearInterval(radioTimer);
    radioTimer = null;
  }
}

function loadRadioStats() {
  fetch("radio-stats", {headers: {"Accept": "application/json"}})
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (payload) {
      lastRadio = payload;
      radioError = payload.error || "";
      if (payload.cell && currentView === "ue-monitoring") {
        radioHistory.push({
          t: Date.now(),
          ul: Number(payload.cell.ul_bitrate) || 0,
          dl: Number(payload.cell.dl_bitrate) || 0
        });
        var cutoff = Date.now() - 3 * 60 * 1000;
        radioHistory = radioHistory.filter(function (point) {
          return point.t >= cutoff;
        });
      }
      paintSimIpSurfaces();
      if (currentView === "ue-monitoring") {
        renderUeMonitoring();
      }
    })
    .catch(function (error) {
      radioError = error.message;
      if (currentView === "ue-monitoring") {
        renderUeMonitoring();
      }
    });
}

function paintSimIpSurfaces() {
  if (typeof renderSimManagement === "function") {
    renderSimManagement();
  }
  if (selectedRouteSimTitle && typeof showRouteSim === "function") {
    showRouteSim(selectedRouteSimTitle);
  }
  if (typeof selectedNode !== "undefined" && selectedNode && selectedNode._node &&
      !selectedNode._node.hub && typeof selectNode === "function") {
    selectNode(selectedNode);
  }
}

function mbps(bits) {
  if (bits === null || bits === undefined || bits === "") {
    return null;
  }
  return (Number(bits) / 1e6).toFixed(2);
}

function radioByImsi() {
  var map = {};
  ((lastRadio && lastRadio.ues) || []).forEach(function (ue) {
    if (ue.imsi) {
      map[String(ue.imsi)] = ue;
    }
  });
  return map;
}

function simImsi(sim) {
  var parameters = unwrapParameters(sim.parameters);
  var connection = unwrapParameters(sim.connection_parameters);
  if (connection.imsi || parameters.imsi) {
    return String(connection.imsi || parameters.imsi);
  }
  if (parameters.plmn && parameters.msin) {
    return String(parameters.plmn) + String(parameters.msin);
  }
  return "";
}

function chartScale(peak) {
  var mega = peak >= 1e6;
  var unit = mega ? 1e6 : 1e3;
  var label = mega ? "Mb/s" : "kb/s";
  var value = peak / unit;
  if (!(value > 0)) {
    return {maxBits: unit, unit: unit, label: label};
  }
  var magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  var fraction = value / magnitude;
  var nice = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 5 ? 5 : 10;
  return {maxBits: nice * magnitude * unit, unit: unit, label: label};
}

function formatRate(bits, unit) {
  var value = bits / unit;
  if (value >= 100) {
    return value.toFixed(0);
  }
  if (value >= 10) {
    return value.toFixed(1);
  }
  return value.toFixed(value >= 1 ? 1 : 2);
}

function formatClock(timestamp) {
  var date = new Date(timestamp);
  function two(value) {
    return (value < 10 ? "0" : "") + value;
  }
  return two(date.getHours()) + ":" + two(date.getMinutes()) + ":" + two(date.getSeconds());
}

function radioChart() {
  if (radioHistory.length < 2) {
    return '<div class="empty">Waiting for samples.</div>';
  }
  var width = 720;
  var height = 176;
  var left = 48;
  var right = 12;
  var top = 14;
  var bottom = 24;
  var plotWidth = width - left - right;
  var plotHeight = height - top - bottom;
  var peak = 0;
  radioHistory.forEach(function (point) {
    peak = Math.max(peak, point.ul, point.dl);
  });
  var scale = chartScale(peak);
  var maxBits = scale.maxBits;
  var start = radioHistory[0].t;
  var end = radioHistory[radioHistory.length - 1].t;
  var span = Math.max(end - start, 1);

  function xOf(timestamp) {
    return left + plotWidth * ((timestamp - start) / span);
  }
  function yOf(bits) {
    return top + plotHeight * (1 - bits / maxBits);
  }
  function line(key) {
    return radioHistory.map(function (point) {
      return xOf(point.t).toFixed(1) + "," + yOf(point[key]).toFixed(1);
    }).join(" ");
  }

  var marks = "";
  var steps = 4;
  var step;
  for (step = 0; step <= steps; step += 1) {
    var bits = maxBits * (step / steps);
    var y = yOf(bits);
    marks += '<line x1="' + left + '" y1="' + y.toFixed(1) + '" x2="' + (left + plotWidth) +
      '" y2="' + y.toFixed(1) + '" stroke="#e3e6ea" stroke-width="1"/>';
    marks += '<text x="' + (left - 6) + '" y="' + y.toFixed(1) +
      '" text-anchor="end" dominant-baseline="middle" fill="#6b7280" font-size="7" font-weight="400" font-family="ui-monospace, monospace">' +
      formatRate(bits, scale.unit) + "</text>";
  }
  var ticks = 4;
  var tick;
  for (tick = 0; tick <= ticks; tick += 1) {
    var timestamp = start + span * (tick / ticks);
    var x = xOf(timestamp);
    var anchor = tick === 0 ? "start" : tick === ticks ? "end" : "middle";
    marks += '<line x1="' + x.toFixed(1) + '" y1="' + top + '" x2="' + x.toFixed(1) +
      '" y2="' + (top + plotHeight) + '" stroke="#eef0f3" stroke-width="1"/>';
    marks += '<text x="' + x.toFixed(1) + '" y="' + (height - 6) +
      '" text-anchor="' + anchor + '" fill="#6b7280" font-size="7" font-weight="400" font-family="ui-monospace, monospace">' +
      formatClock(timestamp) + "</text>";
  }
  marks += '<text x="' + left + '" y="9" fill="#9aa1ab" font-size="7" font-weight="400" font-family="ui-monospace, monospace">' +
    scale.label + "</text>";

  return '<svg class="ue-chart" viewBox="0 0 ' + width + " " + height + '">' +
    marks +
    '<polyline fill="none" stroke="#12a150" stroke-width="2" points="' + line("ul") + '"/>' +
    '<polyline fill="none" stroke="#3b6ef0" stroke-width="2" points="' + line("dl") + '"/>' +
    "</svg>";
}

function fixedOrDash(value, digits) {
  if (value === null || value === undefined || value === "") {
    return TELEMETRY_DASH;
  }
  return Number(value).toFixed(digits);
}

function percentUse(value) {
  if (value === null || value === undefined || value === "") {
    return TELEMETRY_DASH;
  }
  return (Number(value) * 100).toFixed(1);
}

function attachDelta(cell) {
  var current = {
    noMatch: Number(cell.rrc_reject_no_match) || 0,
    noContext: Number(cell.rrc_reject_no_context) || 0,
    setupRequest: Number(cell.rrc_setup_request) || 0,
    setupComplete: Number(cell.rrc_setup_complete) || 0
  };
  var keys = ["noMatch", "noContext", "setupRequest", "setupComplete"];
  if (!attachBaseline || keys.some(function (key) { return current[key] < attachBaseline[key]; })) {
    attachBaseline = current;
  }
  return {
    noMatch: current.noMatch - attachBaseline.noMatch,
    noContext: current.noContext - attachBaseline.noContext,
    setupRequest: current.setupRequest - attachBaseline.setupRequest,
    setupComplete: current.setupComplete - attachBaseline.setupComplete
  };
}

function stationMetricCard(title, hint, body) {
  return '<div class="card"><div class="card-t">' + esc(title) + '</div>' +
    '<div class="card-hint">' + esc(hint) + '</div><div class="ue-m">' + body + '</div></div>';
}

function renderStationStats() {
  var holder = element("ue-station");
  if (!holder) {
    return;
  }
  var cell = lastRadio && lastRadio.cell;
  if (!cell) {
    holder.innerHTML = "";
    return;
  }
  var delta = attachDelta(cell);
  holder.innerHTML =
    stationMetricCard("Load", "Latest sample",
      metric("CPU", fixedOrDash(cell.cpu, 1), "%") +
      metric("UEs", fixedOrDash(cell.ue_count, 1), "") +
      metric("Active UEs", fixedOrDash(cell.ue_active_count, 1), "") +
      metric("UL use", percentUse(cell.ul_use), "%") +
      metric("DL use", percentUse(cell.dl_use), "%")) +
    stationMetricCard("Radio quality", "Latest sample",
      metric("DL errors", fixedOrDash(cell.dl_err, 0), "") +
      metric("UL errors", fixedOrDash(cell.ul_err, 0), "") +
      metric("DL retx", fixedOrDash(cell.dl_retx, 0), "") +
      metric("UL retx", fixedOrDash(cell.ul_retx, 0), "") +
      metric("RX/TX delay", fixedOrDash(cell.rxtx_delay_us, 1), "µs")) +
    stationMetricCard("Attach errors", "Increase since this page was opened",
      metric("Setup requests", String(delta.setupRequest), "") +
      metric("Setup complete", String(delta.setupComplete), "") +
      metric("Rejected, no match", String(delta.noMatch), "") +
      metric("Rejected, no core", String(delta.noContext), ""));
}

function renderUeMonitoring() {
  var sims = simList();
  var enabled = sims.filter(function (sim) {
    return !unwrapParameters(sim.parameters).disable_sim;
  });
  var disabled = sims.length - enabled.length;
  var byImsi = radioByImsi();
  var cell = lastRadio && lastRadio.cell;
  var ues = (lastRadio && lastRadio.ues) || [];
  var onRadio = ues.filter(function (ue) { return ue.connected; }).length;
  var cqis = ues.filter(function (ue) { return ue.cqi !== null && ue.cqi !== undefined; });
  var cqiText = cqis.length ? (cqis.reduce(function (sum, ue) {
    return sum + Number(ue.cqi);
  }, 0) / cqis.length).toFixed(1) : TELEMETRY_DASH;
  var ulText = cell ? (mbps(cell.ul_bitrate) + " / " + mbps(cell.dl_bitrate)) : TELEMETRY_DASH;

  element("ue-status").innerHTML =
    statusCard("blue", ICON.device, "Devices provisioned", sims.length + " SIM",
      "SIM profiles known to the core network.") +
    statusCard("green", ICON.users, "Enabled", enabled.length + " of " + sims.length,
      disabled ? disabled + " SIM disabled in configuration." : "No SIM disabled.") +
    statusCard(onRadio ? "green" : "grey", ICON.signal, "On radio", String(onRadio),
      cqiText === TELEMETRY_DASH ? "No CQI reported." : "Average CQI " + cqiText + ".") +
    statusCard(cell ? "blue" : "grey", ICON.chart, "Cell throughput", ulText,
      cell && cell.gtp_ul_bitrate !== null && cell.gtp_ul_bitrate !== undefined ?
        "Radio uplink / downlink. IP " + mbps(cell.gtp_ul_bitrate) + " / " + mbps(cell.gtp_dl_bitrate) + " Mb/s." :
        (cell ? "Uplink / downlink, Mb/s." : "Waiting for the radio sample."));

  if (!lastRadio || lastRadio.pending) {
    element("ue-note").textContent = "Reading the radio…";
  } else if (radioError) {
    element("ue-note").textContent = radioError + (lastRadio.stale ? " Showing the last sample." : "");
  } else {
    element("ue-note").textContent = "Uplink is shown before downlink. Samples stay in this page only.";
  }
  element("ue-chart").innerHTML = radioChart();
  renderStationStats();

  element("ue-grid").innerHTML = sims.length ? sims.map(function (sim) {
    var parameters = unwrapParameters(sim.parameters);
    var isEnabled = !parameters.disable_sim;
    var imsi = simImsi(sim);
    var live = byImsi[imsi];
    var stateLabel = "Not attached";
    var stateOn = false;
    if (live && live.connected) {
      stateLabel = "On radio";
      stateOn = true;
    } else if (live && live.registered) {
      stateLabel = "Registered";
      stateOn = true;
    }
    var down = liveText(live, "dl_bitrate", 2);
    var up = liveText(live, "ul_bitrate", 2);
    if (down !== TELEMETRY_DASH) {
      down = mbps(live.dl_bitrate);
    }
    if (up !== TELEMETRY_DASH) {
      up = mbps(live.ul_bitrate);
    }
    var received = volumeText(live && live.dl_total_bytes);
    var sent = volumeText(live && live.ul_total_bytes);
    var imei = imeiOf(live);
    var shownIp = assignedSimIp(sim);
    return '<div class="ue">' +
      '<div class="ue-h"><div>' +
      '<div class="ue-n">' + esc(sim.title) + '</div>' +
      simAliasHtml(sim.title) +
      '<div class="ue-id">SIM ' + esc(orDash(imsi)) + '</div>' +
      (imei ? '<div class="ue-id">IMEI ' + esc(imei) + '</div>' : '') +
      '<div class="ue-id">IP ' + esc(orDash(shownIp)) + '</div>' +
      '</div>' +
      '<span class="badge ' + (stateOn ? "b-on" : "b-off") + '">' + esc(stateLabel) + '</span></div>' +
      '<div class="chips">' +
      '<span class="chip">' + (isEnabled ? "Enabled" : "Disabled") + '</span>' +
      (live && live.rat ? '<span class="chip">' + esc(live.rat) + '</span>' : '') +
      (live && live.apn ? '<span class="chip">' + esc(live.apn) + '</span>' : '') +
      (live && live.ip && String(live.ip) !== shownIp ? '<span class="chip">' + esc(live.ip) + '</span>' : '') +
      (live && live.ipv6 ? '<span class="chip">' + esc(live.ipv6) + '</span>' : '') +
      '</div>' +
      '<div class="ue-m">' +
      metric("SNR", liveText(live, "pusch_snr", 1), "dB") +
      metric("DL bitrate", down, "Mb/s") +
      metric("UL bitrate", up, "Mb/s") +
      metric("CQI", liveText(live, "cqi", 0), "") +
      metric("DL MCS", liveText(live, "dl_mcs", 1), "") +
      metric("UL MCS", liveText(live, "ul_mcs", 1), "") +
      metric("Path loss", liveText(live, "ul_path_loss", 1), "dB") +
      metric("Timing advance", liveText(live, "initial_ta", 0), "TS") +
      metric("DL volume", received.text, received.unit) +
      metric("UL volume", sent.text, sent.unit) +
      '</div></div>';
  }).join("") : '<div class="empty">No SIM provisioned.<br>Add one from SIM Management.</div>';

  element("ue-expert").innerHTML = sims.length ?
    '<table class="tbl"><thead><tr><th>Device name</th><th>IMSI</th><th>State</th>' +
    '<th>Assigned IP</th><th>IP</th><th>CQI</th><th>Uplink</th><th>Downlink</th><th>SNR</th></tr></thead><tbody>' +
    sims.map(function (sim) {
      var live = byImsi[simImsi(sim)];
      var stateLabel = live && live.connected ? "On radio" : (live && live.registered ? "Registered" : "Not attached");
      return '<tr><td class="t-name">' + esc(sim.title) + '</td>' +
        '<td class="t-mono">' + esc(orDash(simImsi(sim))) + '</td>' +
        '<td>' + esc(stateLabel) + '</td>' +
        '<td class="t-mono">' + esc(orDash(assignedSimIp(sim))) + '</td>' +
        '<td class="t-mono">' + esc(live && live.ip ? live.ip : TELEMETRY_DASH) + '</td>' +
        '<td class="t-mono">' + esc(live && live.cqi !== null && live.cqi !== undefined ? String(Math.round(live.cqi)) : TELEMETRY_DASH) + '</td>' +
        '<td class="t-mono">' + esc(live && live.ul_bitrate !== null && live.ul_bitrate !== undefined ? mbps(live.ul_bitrate) : TELEMETRY_DASH) + '</td>' +
        '<td class="t-mono">' + esc(live && live.dl_bitrate !== null && live.dl_bitrate !== undefined ? mbps(live.dl_bitrate) : TELEMETRY_DASH) + '</td>' +
        '<td class="t-mono">' + esc(live && live.pusch_snr !== null && live.pusch_snr !== undefined ? Number(live.pusch_snr).toFixed(1) : TELEMETRY_DASH) + '</td></tr>';
    }).join("") + '</tbody></table>' :
    '<div class="empty">No SIM provisioned.</div>';
}

function metric(label, value, unit) {
  return '<div><div class="m-k">' + esc(label) + '</div>' +
    '<div class="m-v">' + esc(value) + '<div class="m-u">' + esc(unit) + '</div></div></div>';
}

function liveText(live, key, digits) {
  if (!live || live[key] === null || live[key] === undefined || live[key] === "") {
    return TELEMETRY_DASH;
  }
  var number = Number(live[key]);
  if (digits === 0) {
    return String(Math.round(number));
  }
  return number.toFixed(digits);
}

function volumeText(value) {
  if (value === null || value === undefined || value === "") {
    return {text: TELEMETRY_DASH, unit: "B"};
  }
  var number = Number(value);
  if (number < 1024) {
    return {text: String(Math.round(number)), unit: "B"};
  }
  if (number < 1024 * 1024) {
    return {text: (number / 1024).toFixed(1), unit: "KB"};
  }
  if (number < 1024 * 1024 * 1024) {
    return {text: (number / (1024 * 1024)).toFixed(1), unit: "MB"};
  }
  return {text: (number / (1024 * 1024 * 1024)).toFixed(2), unit: "GB"};
}

function imeiOf(live) {
  if (!live || !live.imeisv) {
    return "";
  }
  var value = String(live.imeisv);
  if (value.length > 14) {
    value = value.slice(0, value.length - 2);
  }
  return value;
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

registerScreen({
  id: "ue-monitoring",
  title: "UE Monitoring",
  render: renderUeMonitoring,
  enter: startRadioPoll,
  refresh: loadRadioStats
});
