"use strict";

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

registerScreen({
  id: "events",
  title: "Events",
  render: renderEvents
});
registerScreen({
  id: "settings",
  title: "Settings",
  render: renderSettings
});
