"use strict";

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

registerScreen({
  id: "core-network",
  title: "Core Network",
  render: renderCoreNetwork
});
