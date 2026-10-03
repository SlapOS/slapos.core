"use strict";

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

registerScreen({
  id: "cells",
  title: "Cells",
  render: renderCells
});
