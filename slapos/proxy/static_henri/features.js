// Screens shown in the menu, in display order.
// Remove an id to hide that screen and skip its enter/render/refresh.
// "routes" only hides the routing table: SIM badges and Production Set
// still read the kernel table through henri-core.js.
window.HENRI_SCREENS = [
  "dashboard",
  "ue-monitoring",
  "production-set",
  "cells",
  "core-network",
  "routes",
  "sim-management",
  "events",
  "settings"
];

window.Henri = {screens: {}};
