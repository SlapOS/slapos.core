/*jslint nomen: true, indent: 2, maxerr: 3, unparam: true */
/*global window, document, rJS, RSVP, Node, asBoolean , ensureArray,
         mergeGlobalActionWithRawActionList, domsugar*/
(function (window, document, rJS, RSVP, Node, domsugar) {
  "use strict";

  rJS(window)
    .setState({
      visible: false
    })
    //////////////////////////////////////////////
    // acquired method
    //////////////////////////////////////////////
    .declareAcquiredMethod("getUrlForList", "getUrlForList")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")
    .declareAcquiredMethod("getTranslationDict", "getTranslationDict")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("getUrlParameter", "getUrlParameter")
    .declareAcquiredMethod("renderEditorPanel", "renderEditorPanel")


    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod('toggle', function toggle() {
      return this.changeState({
        visible: !this.state.visible
      });
    })
    .declareMethod('close', function close() {
      return this.changeState({
        visible: false
      });
    })

    .declareMethod('render', function render(options) {
      return this.changeState({
        global: true,
        editable: true,
        jio_key: options.jio_key
      });
    })
    .onStateChange(function onStateChange(modification_dict) {
      var i,
        context = this,
        gadget = this,
        jio_key = modification_dict.jio_key,
        translation_index_list = [
          'Services',
          'Dashboard',
          'Login Account',
          'Tickets',
          'Sites',
          'Invoices',
          'Servers',
          'Networks',
          'Language',
          'Logout'
        ],
        queue = new RSVP.Queue();

      if (modification_dict.hasOwnProperty("visible")) {
        if (this.state.visible) {
          if (!this.element.classList.contains('visible')) {
            this.element.classList.toggle('visible');
          }
        } else {
          if (this.element.classList.contains('visible')) {
            this.element.classList.remove('visible');
          }
        }
      }
      if (modification_dict.hasOwnProperty("editable")) {
        queue
          // Update the global links
          .push(function () {
            return RSVP.hash({
              url_list: gadget.getUrlForList([
                {command: 'display', options: {page: "slap_service_list", editable: true}},
                {command: 'display', options: {page: "slapos", editable: true}},
                {command: 'display', options: {page: "slap_person_view", editable: true}},
                {command: 'display', options: {page: "slap_ticket_list", editable: true}},
                {command: 'display', options: {page: "slap_site_list", editable: true}},
                {command: 'display', options: {page: "slap_invoice_list", editable: true}},
                {command: 'display', options: {page: "slap_compute_node_list", editable: true}},
                {command: 'display', options: {page: "slap_network_list", editable: true}},
                {command: 'display', options: {page: "slap_language_view"}},
                {command: 'display', options: {page: "logout"}}
              ]),
              translation_list: gadget.getTranslationList(translation_index_list)
            });
          })
          .push(function (result_dict) {
            var element_list = [],
              icon_and_key_list = [
                'home', 'l',
                'gears', 'h',
                'user', 'p',
                'comments', 't',
                'map-marker', 'k',
                'credit-card', 'i',
                'database', 'c',
                'globe', 'n',
                'language', 'a',
                'power-off', 'o'
              ];

            for (i = 0; i < result_dict.url_list.length; i += 1) {
              // <li><a href="URL" class="ui-btn-icon-left ui-icon-ICON" data-i18n="TITLE" accesskey="KEY"></a></li>
              element_list.push(domsugar('li', [
                domsugar('a', {
                  href: result_dict.url_list[i],
                  'class': 'ui-btn-icon-left ui-icon-' + icon_and_key_list[2 * i],
                  accesskey: icon_and_key_list[2 * i + 1],
                  text: result_dict.translation_list[i],
                  'data-i18n': translation_index_list[i]
                })
              ]));
            }

            return domsugar(gadget.element.querySelector("ul"),
                     [domsugar(null, element_list)]);
          })
          .push(function () {
            return gadget.getDeclaredGadget('erp5_panel_shortcut');
          })
          .push(function (shortcut_gadget) {
            // Ensure links are updated
            return shortcut_gadget.render({update: 1});
          });
      }
      // Check for Alerts to pop
      if (!(jio_key === undefined || jio_key === null)) {
        queue
          .push(function () {
            return context.calculateContextualHelpList(jio_key);
          })
          .push(function () {
            return context.calculateMyAttentionPointList(jio_key, false);
          });
      }
      return queue;
    })

    /////////////////////////////////////////////////////////////////
    // declared services
    /////////////////////////////////////////////////////////////////
    .onEvent('click', function click(evt) {
      if ((evt.target.nodeType === Node.ELEMENT_NODE) &&
          (evt.target.tagName === 'BUTTON')) {
        return this.toggle();
      }
      if (this.element.querySelector('a.attention-point-link') === evt.target) {
        evt.preventDefault();
        return this.calculateMyAttentionPointList(this.state.jio_key, true);
      }
    }, false, false)

    .allowPublicAcquisition('notifyChange', function notifyChange() {
      // Typing a search query should not modify the header status
      return;
    })

    .allowPublicAcquisition("notifyFocus", function notifyFocus() {
      // All html5 fields in ERP5JS triggers this method when focus
      // is triggered. This is usefull to display error text.
      // But, in the case of panel, we don't need to handle anything.
      return;
    })
    .allowPublicAcquisition("notifyBlur", function notifyBlur() {
      // All html5 fields in ERP5JS triggers this method when blur
      // is triggered now. This is usefull to display error text.
      // But, in the case of panel, we don't need to handle anything.
      return;
    })


    .declareJob("calculateContextualHelpList", function (jio_key) {
      var context = this,
        queue = new RSVP.Queue(),
        contextual_help_dl = context.element.querySelector("dl.dl-contextual-help");
      return queue
        .push(function () {
          return context.getSetting('hateoas_url');
        })
        .push(function (hateoas_url) {
          if (jio_key === false || jio_key === undefined || jio_key === null) {
            return [];
          }
          return context.jio_getAttachment(
            jio_key,
            hateoas_url + jio_key + '/Base_getContextualHelpList'
          );
        })
        .push(function (contextual_help_list) {
          var i,
            contextual_help_element_list = [];
          if (contextual_help_list.length > 0) {
            if (document.querySelector('.contextual-help-link') === null) {
              contextual_help_element_list.push(domsugar("dt",
                {
                  "class": "ui-btn-icon-left ui-icon-question",
                  "data-i18n": "Help",
                  "text": "Help"
                })
                );
              for (i = 0; i < contextual_help_list.length; i += 1) {
                contextual_help_element_list.push(
                  domsugar("dd", {"class": "document-listview"},
                    [
                      domsugar("a", {
                        "class": "help",
                        "target": "_blank",
                        "data-i18n": contextual_help_list[i]["data-i18n"],
                        "href": contextual_help_list[i].href,
                        "text": contextual_help_list[i].title
                      })])
                );
              }
            }
          }
          return domsugar(contextual_help_dl,
                {"class": "dl-contextual-help"},
                contextual_help_element_list);
        });
    })
    .declareJob("calculateMyAttentionPointList", function (jio_key, force_open) {
      var context = this,
        attention_point_ul = context.element.querySelector('ul.ul-attention-point'),
        seen_attention_point_dict = JSON.parse(window.sessionStorage.getItem('seen_attention_point_dict') || "{}");
      return context.getSetting('hateoas_url')
        .push(function (hateoas_url) {
          if (jio_key === false || jio_key === undefined || jio_key === null) {
            return [[], 'No Alert'];
          }
          return RSVP.all([
            context.jio_getAttachment(
              jio_key,
              hateoas_url + jio_key + '/Base_getAttentionPointList'
            ),
            context.getTranslationList([
              'No Alert!',
              'Warnings'])
          ]);
        })
        .push(function (result_list) {
          var attention_point_list = result_list[0],
            no_alert_caption = result_list[1][0];
          if (attention_point_list.length > 0) {
            domsugar(attention_point_ul, {class: 'ul-attention-point'}, [
              domsugar(
                "li",
                {},
                [
                  domsugar("a",
                    {
                      "class": "ui-btn-icon-notext ui-icon-warning attention-point-link",
                      "text": result_list[1][1] + " (" + attention_point_list.length + ")"
                    })
                ]
              )]);
            if (force_open || (JSON.stringify(seen_attention_point_dict[jio_key]) !== JSON.stringify(attention_point_list))) {
              seen_attention_point_dict[jio_key] = attention_point_list;
              window.sessionStorage.setItem('seen_attention_point_dict', JSON.stringify(seen_attention_point_dict));
              return context.renderEditorPanel("gadget_erp5_attention_point.html", {
                attention_point_list: attention_point_list
              });
            }
          } else {
            domsugar(attention_point_ul,
              {class: 'ul-attention-point'},
              [domsugar("li")]);

            if (force_open) {
              return context.renderEditorPanel("gadget_erp5_attention_point.html", {
                attention_point_list: [[no_alert_caption, 'no-alert']]
              });
            }
          }
        });
    });

}(window, document, rJS, RSVP, Node, domsugar));
