/*global window, rJS, RSVP, UriTemplate */
/*jslint indent: 2, maxerr: 3, nomen: true */
(function (window, RSVP, UriTemplate) {
  "use strict";
  window.getSettingMe = function getSettingMe(gadget) {
    return new RSVP.Queue()
      .push(function () {
        return gadget.getSetting("me");
      })
      .push(function (me) {
        try {
          gadget.jio_get(me);
        } catch (error) {
          me = undefined;
        } finally {
          return me;
        }
      })
      .push(function (me) {
        if (me === undefined) {
          var logout_url_template;

          return gadget.jio_getAttachment('acl_users', 'links')
            .push(function (links) {
              logout_url_template = links._links.logout.href;
              return gadget.getUrlFor({
                command: 'display',
                absolute_url: true,
                options: {}
              });
            })
            .push(function (came_from) {
              return gadget.redirect({
                command: 'raw',
                options: {
                  url: UriTemplate.parse(logout_url_template).expand({came_from: came_from})
                }
              });
            });
        }
        return me;
      });
  };
}(window, RSVP, UriTemplate));