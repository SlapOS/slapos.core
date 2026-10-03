"use strict";

function simByTitle(title) {
  var found = null;
  simList().some(function (sim) {
    if (sim.title === title) {
      found = sim;
      return true;
    }
    return false;
  });
  return found;
}

function routeSimButtons(route) {
  var owners = simsForPrefix(normalizeCidr(route.destination));
  if (!owners.length) {
    return "—";
  }
  var buttons = owners.map(function (sim) {
    var selected = selectedRouteSimTitle === sim.title ? " on" : "";
    return '<button type="button" class="sim-link' + selected + '" data-sim-title="' +
      esc(sim.title) + '">' + esc(sim.title) + "</button>";
  }).join(", ");
  if (owners.length > 1) {
    buttons += ' <span class="sim-conflict">(conflit)</span>';
  }
  return buttons;
}

function clearRouteSim() {
  selectedRouteSimTitle = null;
  element("route-dev-idx").textContent = "—";
  element("route-dev-b").innerHTML =
    '<div class="empty">Aucune SIM sélectionnée.<br>Cliquez une SIM liée à une route.</div>';
  element("route-dev-f").classList.add("hidden");
  element("route-dev-note").classList.add("hidden");
}

function showRouteSim(title) {
  var sim = simByTitle(title);
  if (!sim) {
    clearRouteSim();
    return;
  }
  selectedRouteSimTitle = sim.title;
  var parameters = unwrapParameters(sim.parameters);
  var connection = unwrapParameters(sim.connection_parameters);
  var meta = readLabel(sim.title);
  var enabled = !parameters.disable_sim;
  var routeBlock = "";
  if (simDeclaredRoutes(sim).length) {
    routeBlock = '<div style="margin-top:14px"><div class="eyebrow" style="margin-bottom:8px">Routes</div>' +
      simRouteBadges(sim) + "</div>";
  }
  element("route-dev-idx").textContent = enabled ? "ENABLED" : "DISABLED";
  element("route-dev-b").innerHTML =
    '<div class="dev-n">' + esc(meta.label || sim.title) + "</div>" +
    '<div class="dev-m">' + esc(connection.imsi || parameters.imsi || sim.title) + "</div>" +
    (enabled ? '<div class="dev-live">ON THE SET</div>' : "") +
    '<div style="margin-top:14px">' +
    devRow("Device name", sim.title) +
    devRow("IMSI", orDash(connection.imsi || parameters.imsi)) +
    devRow("MSIN", orDash(parameters.msin)) +
    devRow("Network code", orDash(parameters.plmn)) +
    devRow("Algorithm", orDash(parameters.sim_algo)) +
    devRow("Device group", apnText()) +
    "</div>" + routeBlock;
  element("route-dev-f").classList.remove("hidden");
  element("route-dev-note").classList.remove("hidden");
  document.querySelectorAll("#routes-body .sim-link").forEach(function (button) {
    button.classList.toggle("on", button.getAttribute("data-sim-title") === sim.title);
  });
}
function routeCells(route) {
  var destination = route.destination === "default" ? "Passerelle par défaut" : route.destination;
  var via = route.via || "lien direct";
  var state = route.linkdown ? "arrêtée" : (route.type || "active");
  return [destination, via, route.iface || "—", route.source || "—", state];
}

function routeTable(routes) {
  if (!routes.length) {
    return '<div class="empty">Aucune route.</div>';
  }
  var head = ["Destination", "Via", "Interface", "Source", "État", "SIM"].map(function (label) {
    return "<th>" + esc(label) + "</th>";
  }).join("");
  var body = routes.map(function (route) {
    return "<tr>" + routeCells(route).map(function (value) {
      return "<td>" + esc(value) + "</td>";
    }).join("") + "<td>" + routeSimButtons(route) + "</td></tr>";
  }).join("");
  return '<table class="tbl"><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table>";
}

function routeFamilyCard(title, text) {
  var groups = splitRouteGroups(parseRouteText(text));
  return '<div class="card" style="margin-bottom:14px">' +
    '<div class="card-t">' + esc(title) + "</div>" +
    '<div class="eyebrow" style="margin:12px 0 8px">Sortie</div>' +
    routeTable(groups.defaults) +
    '<div class="eyebrow" style="margin:16px 0 8px">Réseaux locaux actifs</div>' +
    routeTable(groups.active) +
    '<details class="fold" style="margin-top:14px"><summary>Le reste (' + groups.rest.length + ")</summary>" +
    routeTable(groups.rest) +
    "</details>" +
    '<details class="fold"><summary>Sortie brute</summary><pre class="raw">' + esc(text || "") + "</pre></details>" +
    "</div>";
}

function paintOsRoutes(payload) {
  var container = element("routes-body");
  if (payload.error) {
    container.innerHTML = '<div class="card"><div class="empty">' + esc(payload.error) + "</div></div>";
    return;
  }
  container.innerHTML = routeFamilyCard("IPv4", payload.ipv4) + routeFamilyCard("IPv6", payload.ipv6);
}

if (element("routes-refresh")) {
  element("routes-refresh").addEventListener("click", loadOsRoutes);
}
if (element("routes-body")) {
  element("routes-body").addEventListener("click", function (event) {
    var button = event.target.closest(".sim-link");
    if (!button) {
      return;
    }
    showRouteSim(button.getAttribute("data-sim-title"));
  });
}
if (element("route-dev-edit")) {
  element("route-dev-edit").addEventListener("click", function () {
    var sim = simByTitle(selectedRouteSimTitle);
    if (sim) {
      openEditSimModal(sim);
    }
  });
}
if (element("route-dev-disable")) {
  element("route-dev-disable").addEventListener("click", function () {
    var sim = simByTitle(selectedRouteSimTitle);
    if (sim) {
      setSimEnabled(sim, false);
    }
  });
}

registerScreen({
  id: "routes",
  title: "Routes",
  render: function () {
    if (lastOsPayload) {
      paintOsRoutes(lastOsPayload);
    }
  },
  enter: loadOsRoutes,
  refresh: loadOsRoutes
});
