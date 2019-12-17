/*global window, rJS, RSVP, UriTemplate */
/*jslint indent: 2, maxerr: 3, nomen: true */
(function (window, RSVP, UriTemplate) {
  "use strict";
  function redirectToLoginPage(gadget) {
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

  window.getSettingMe = function getSettingMe(gadget) {
    return new RSVP.Queue()
      .push(function () {
        return gadget.getSetting("me");
      })
      .push(function (me) {
        return RSVP.all([me, gadget.jio_get(me)]);
      })
      .push(function (list) {
        if (list[0] === undefined) {
          return redirectToLoginPage(gadget);
        }
        return list[0];
      })
      .push(undefined, function (error) {
        return redirectToLoginPage(gadget);
      });
  };
  window.getValidDocument = function getValidDocument(gadget, jio_key) {
    return new RSVP.Queue()
      .push(function () {
        return gadget.jio_get(jio_key);
      })
      .push(undefined, function (error) {
        return {"portal_type": "access_denied"};
      });
  };
}(window, RSVP, UriTemplate));