"use strict";

function renderAllViews() {
  (window.HENRI_SCREENS || []).forEach(function (id) {
    var screen = window.Henri.screens[id];
    if (screen && screen.render) {
      screen.render();
    }
  });
}

function viewFromHash() {
  return String(window.location.hash || "").replace(/^#\/?/, "");
}

function setActiveView(view) {
  var enabled = window.HENRI_SCREENS || [];
  if (enabled.indexOf(view) === -1) {
    view = enabled[0] || "dashboard";
  }
  var previous = currentView;
  var previousScreen = window.Henri.screens[previous];
  currentView = view;
  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".view").forEach(function (section) {
    section.classList.toggle("active", section.id === "view-" + view);
  });
  var screen = window.Henri.screens[view];
  element("crumb").textContent = screen && screen.title ? screen.title : view;
  element("scroll").scrollTop = 0;
  if (previous !== view && previousScreen && previousScreen.leave) {
    previousScreen.leave();
  }
  if (screen && screen.enter) {
    screen.enter();
  }
  if (viewFromHash() !== view) {
    window.location.hash = "#/" + view;
  }
}

function applyScreenVisibility() {
  var enabled = {};
  (window.HENRI_SCREENS || []).forEach(function (id) {
    enabled[id] = true;
  });
  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.classList.toggle("hidden", !enabled[button.dataset.view]);
  });
  document.querySelectorAll(".view").forEach(function (section) {
    var id = section.id.replace(/^view-/, "");
    section.classList.toggle("hidden", !enabled[id]);
  });
}

applyScreenVisibility();

window.addEventListener("hashchange", function () {
  var view = viewFromHash();
  if (view && view !== currentView) {
    setActiveView(view);
  }
});

document.querySelectorAll(".nav-item").forEach(function (button) {
  button.addEventListener("click", function () {
    if (button.classList.contains("hidden")) {
      return;
    }
    setActiveView(button.dataset.view);
  });
});

element("collapse").addEventListener("click", function () {
  element("app").classList.toggle("collapsed");
});

element("refresh").addEventListener("click", function () {
  loadAllServices();
  var screen = window.Henri.screens[currentView];
  if (screen && screen.refresh) {
    screen.refresh();
  }
});

window.setInterval(function () {
  secondsSinceLoad += 1;
  element("clock").textContent =
    pad(Math.floor(secondsSinceLoad / 3600)) + ":" +
    pad(Math.floor(secondsSinceLoad / 60) % 60) + ":" +
    pad(secondsSinceLoad % 60);
}, 1000);

setActiveView(viewFromHash() || "dashboard");
if (typeof startRadioPoll === "function") {
  startRadioPoll();
}
updateLivePill();
if (typeof loadProductionSet === "function") {
  loadProductionSet();
}
loadAllServices();
