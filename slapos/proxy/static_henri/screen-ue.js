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
      if (payload.cell) {
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

function radioChart() {
  if (radioHistory.length < 2) {
    return '<div class="empty">Waiting for samples.</div>';
  }
  var width = 640;
  var height = 120;
  var pad = 8;
  var max = 1;
  radioHistory.forEach(function (point) {
    max = Math.max(max, point.ul, point.dl);
  });
  function line(key) {
    return radioHistory.map(function (point, index) {
      var x = pad + (width - 2 * pad) * (index / (radioHistory.length - 1));
      var y = height - pad - (height - 2 * pad) * (point[key] / max);
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }
  return '<svg class="ue-chart" viewBox="0 0 ' + width + " " + height +
    '" preserveAspectRatio="none">' +
    '<polyline fill="none" stroke="#12a150" stroke-width="2" points="' + line("ul") + '"/>' +
    '<polyline fill="none" stroke="#3b6ef0" stroke-width="2" points="' + line("dl") + '"/>' +
    "</svg>";
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
    var snr = live && live.pusch_snr !== null && live.pusch_snr !== undefined ? Number(live.pusch_snr).toFixed(1) : TELEMETRY_DASH;
    var down = live && live.dl_bitrate !== null && live.dl_bitrate !== undefined ? mbps(live.dl_bitrate) : TELEMETRY_DASH;
    var up = live && live.ul_bitrate !== null && live.ul_bitrate !== undefined ? mbps(live.ul_bitrate) : TELEMETRY_DASH;
    var cqi = live && live.cqi !== null && live.cqi !== undefined ? String(Math.round(live.cqi)) : TELEMETRY_DASH;
    var mcs = (live && live.dl_mcs !== null && live.dl_mcs !== undefined) ?
      (Number(live.dl_mcs).toFixed(1) + " / " + (live.ul_mcs === null || live.ul_mcs === undefined ? TELEMETRY_DASH : Number(live.ul_mcs).toFixed(1))) :
      TELEMETRY_DASH;
    var ta = live && live.initial_ta !== null && live.initial_ta !== undefined ? String(Math.round(live.initial_ta)) : TELEMETRY_DASH;
    return '<div class="ue">' +
      '<div class="ue-h"><div>' +
      '<div class="ue-n">' + esc(sim.title) + '</div>' +
      '<div class="ue-id">SIM ' + esc(orDash(imsi)) + '</div></div>' +
      '<span class="badge ' + (stateOn ? "b-on" : "b-off") + '">' + esc(stateLabel) + '</span></div>' +
      '<div class="chips">' +
      '<span class="chip">' + (isEnabled ? "Enabled" : "Disabled") + '</span>' +
      (live && live.rat ? '<span class="chip">' + esc(live.rat) + '</span>' : '') +
      (live && live.ip ? '<span class="chip">' + esc(live.ip) + '</span>' : '') +
      '</div>' +
      '<div class="ue-m">' +
      metric("SNR", snr, "dB") +
      metric("Receiving", down, "Mb/s") +
      metric("Sending", up, "Mb/s") +
      metric("Radio quality", cqi, "CQI") +
      metric("Downlink / uplink", mcs, "MCS") +
      metric("Timing advance", ta, "TS") +
      '</div></div>';
  }).join("") : '<div class="empty">No SIM provisioned.<br>Add one from SIM Management.</div>';

  element("ue-expert").innerHTML = sims.length ?
    '<table class="tbl"><thead><tr><th>Device name</th><th>IMSI</th><th>State</th>' +
    '<th>IP</th><th>CQI</th><th>Uplink</th><th>Downlink</th><th>SNR</th></tr></thead><tbody>' +
    sims.map(function (sim) {
      var live = byImsi[simImsi(sim)];
      var stateLabel = live && live.connected ? "On radio" : (live && live.registered ? "Registered" : "Not attached");
      return '<tr><td class="t-name">' + esc(sim.title) + '</td>' +
        '<td class="t-mono">' + esc(orDash(simImsi(sim))) + '</td>' +
        '<td>' + esc(stateLabel) + '</td>' +
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
  leave: stopRadioPoll,
  refresh: loadRadioStats
});
