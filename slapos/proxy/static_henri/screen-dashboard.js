"use strict";

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

registerScreen({
  id: "dashboard",
  title: "Dashboard",
  render: renderDashboard
});
