/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("jio_post", "jio_post")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .allowPublicAcquisition('notifySubmit', function () {
      return this.triggerSubmit();
    })

    .onEvent('submit', function () {
      var gadget = this;
      return gadget.notifySubmitting()
        .push(function () {
          return gadget.getDeclaredGadget('form_view');
        })
        .push(function (form_gadget) {
          return form_gadget.getContent();
        })
        .push(function (doc) {
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              return gadget.jio_putAttachment(doc.relative_url,
                url + doc.relative_url + "/SoftwareRelease_requestHostingSubscription", doc);
            });
        })
        .push(function () {
          return gadget.notifySubmitted({message: gadget.message_tranlation, status: 'success'})
            .push(function () {
              // Workaround, find a way to open document without break gadget.
              return gadget.redirect({"command": "change",
                                    "options": {"jio_key": "/", "page": "slap_service_list"}});
            });
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    // prevent render from being called several times by using "onStateChange"
    // which won't be called several times if options didn't change
    // also use a declareJob to let the function finish immediately
    // (gadget.redirect is actually waiting indefinitely) so that parent is
    // happy and doesn't try to call render again
    .declareMethod("render", function (options) {
      var gadget = this,
        translation_list = [
          "New service created.",
          "Intent not supported",
          "Requesting a service…",
          "Instance"
        ];
      return new RSVP.Queue()
        .push(function () {
          return gadget.updatePanel({
            jio_key: false
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.changeState(options),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          gadget.message_tranlation = result[1][0];
          gadget.error_translation = result[1][1];
          gadget.page_title_translation = result[1][2];
          gadget.software_title_translation = result[1][3];
        });
    })
    .onStateChange(function (options) {
      this.deferRender(options);
    })
    .declareJob("deferRender", function (options) {
      var gadget = this;
      if (options.intent !== "request") {
        throw new Error(gadget.error_translation);
      }
      return new RSVP.Queue()
        .push(function () {
          return gadget.updateHeader({
            page_title: gadget.page_title_translation
          });
        })
        .push(function () {
          return gadget.getSetting("hateoas_url")
            .push(function (url) {
              var get_attachement_url = url + "/SoftwareProduct_getSoftwareReleaseAsHateoas?software_release=" + options.software_release;
              if (options.strict === "True") {
                get_attachement_url = get_attachement_url + "&strict:int=1";
              }
              return gadget.jio_getAttachment("/", get_attachement_url);
            });
        })
        .push(function (jio_key) {
          if (options.auto === undefined) {
            return gadget.redirect({"command": "change",
              "options": {"jio_key": jio_key, "page": "slap_add_hosting_subscription",
                          "title": options.title}});
          }
          // The auto is set, so we move foward to auto request the SR
          options.jio_key = jio_key;
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.jio_get(jio_key),
            gadget.getSetting("hateoas_url")
          ]);
        })
        .push(function (result) {
          var software_release = result[1],
            url = result[2],
            doc = {
              url_string: software_release.url_string,
              title: options.software_title ? options.software_title: gadget.software_title_translation + "{uid}",
              relative_url: options.jio_key
            };
          if (options.software_type) {
            doc.software_type = options.software_type;
          }
          if (options.text_content) {
            doc.text_content = options.text_content;
          }
          if (options.shared) {
            doc.shared = options.shared;
          }
          if (options.sla_xml) {
            doc.sla_xml = options.sla_xml;
          }
          return gadget.notifySubmitting()
            .push(function () {
              var query = [];
              query.push("title=" + encodeURIComponent(doc.title));

              if (doc.software_type) {
                query.push("software_type=" + encodeURIComponent(doc.software_type));
              }
              if (doc.shared) {
                query.push("shared:int=" + encodeURIComponent(doc.shared));
              }
              if (doc.text_content) {
                query.push("text_content=" + encodeURIComponent(doc.text_content));
              }
              if (doc.sla_xml) {
                query.push("sla_xml=" + encodeURIComponent(doc.sla_xml));
              }
              return gadget.jio_getAttachment(doc.relative_url,
                url + doc.relative_url + "/SoftwareRelease_requestHostingSubscription?" + query.join("&"));
            })
            .push(function (key) {
              return gadget.notifySubmitted({message: gadget.message_tranlation, status: 'success'})
                .push(function () {
                  // Workaround, find a way to open document without break gadget.
                  return gadget.redirect({"command": "change",
                                  "options": {"jio_key": key, "page": "slap_controller"}});
                });
            });
        });
    });
}(window, rJS, RSVP));
