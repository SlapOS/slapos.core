/*global document, window, rJS */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (document, window, rJS) {
  "use strict";

  rJS(window)

    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_put", "jio_put")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("redirect", "redirect")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition('notifySubmit', function () {
      return this.triggerSubmit();
    })
    .allowPublicAcquisition('updateDocument', function (param_list) {
      var gadget = this, property,
        content = param_list[0], doc = {};
      for (property in content) {
        if ((content.hasOwnProperty(property)) &&
            // Remove undefined keys added by Gadget fields
            (property !== "undefined") &&
            // Remove listboxes UIs
            (property !== "listbox_uid:list") &&
            // Remove default_*:int keys added by ListField
            !(property.endsWith(":int") && property.startsWith("default_"))) {
          doc[property] = content[property];
        }
      }
      return gadget.jio_put(gadget.state.jio_key, doc)
        .push(function () {
          return doc;
        });
    })
    .declareMethod('triggerSubmit', function () {
      return this.getDeclaredGadget('fg')
        .push(function (g) {
          return g.triggerSubmit();
        });
    })

    .declareMethod("render", function (options) {
      var gadget = this,
        child_gadget_url;

      return window.getValidDocument(gadget, options.jio_key)
        .push(function (result) {

          if (result.portal_type === "Support Request Module") {
            child_gadget_url = "gadget_erp5_page_slap_ticket_list.html";
          } else if (result.portal_type === "Instance Tree Module") {
            child_gadget_url = "gadget_erp5_page_slap_service_list.html";
          } else if (result.portal_type === "Accounting Transaction Module") {
            child_gadget_url = "gadget_erp5_page_slap_invoice_list.html";
          } else if (result.portal_type === "Compute Node Module") {
            child_gadget_url = "gadget_erp5_page_slap_compute_node_list.html";
          } else if (result.portal_type === "Organisation Module") {
            child_gadget_url = "gadget_erp5_page_slap_site_list.html";
          } else if (result.portal_type === "Computer Network Module") {
            child_gadget_url = "gadget_erp5_page_slap_network_list.html";
          } else if ((result.portal_type === "Organisation") &&
                     result.role === "host") {
            child_gadget_url = "gadget_erp5_page_slap_site_view.html";
          } else if (result.portal_type !== undefined) {
            child_gadget_url = 'gadget_erp5_page_slap_' +
              result.portal_type.replace(/ /g, '_').toLowerCase() +
              '_view.html';
          } else {
            throw new Error('Can not display document: ' + options.jio_key);
          }

          if (child_gadget_url === 'gadget_erp5_page_slap_access_denied_view.html') {
            // if user try to access a document without correct permission
            // user will be redirected to this page, in this case, set the jio_key
            // to null to avoid some further processing.
            options.jio_key = null;
          }
          return gadget.changeState({
            jio_key: options.jio_key,
            doc: result,
            child_gadget_url: child_gadget_url,
            editable: options.editable
          });
        });
    })
    .onStateChange(function () {
      var fragment = document.createElement('div'),
        gadget = this;

      // Clear first to DOM, append after to reduce flickering/manip
      while (this.element.firstChild) {
        this.element.removeChild(this.element.firstChild);
      }
      this.element.appendChild(fragment);

      return gadget.declareGadget(gadget.state.child_gadget_url, {element: fragment,
                                                                  scope: 'fg'})
        .push(function (form_gadget) {
          return form_gadget.render({
            jio_key: gadget.state.jio_key,
            doc: gadget.state.doc,
            editable: gadget.state.editable
          });
        })
        .push(function () {
          return gadget.updatePanel({jio_key: gadget.state.jio_key});
        });
    });

}(document, window, rJS));