/*global window, rJS */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("redirect", "redirect")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////

    .declareMethod("render", function (options) {
      // Open the ticket directly
      return this.redirect({
        "command": "change",
        "options": {"jio_key": options.doc.follow_up}
      });
    });
}(window, rJS));