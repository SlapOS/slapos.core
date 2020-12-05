/*jslint nomen: true, indent: 2, maxerr: 3 */
/*global window, document, rJS, Handlebars, RSVP, Node, loopEventListener */
(function (window, document, rJS, Handlebars, RSVP, Node, loopEventListener) {
  "use strict";

  /////////////////////////////////////////////////////////////////
  // temlates
  /////////////////////////////////////////////////////////////////
  // Precompile templates while loading the first gadget instance
  var gadget_klass = rJS(window),
    template_element = gadget_klass.__template_element,
    panel_template_header = Handlebars.compile(template_element
                         .getElementById("panel-template-header")
                         .innerHTML),
    panel_template_body = Handlebars.compile(template_element
                         .getElementById("panel-template-body")
                         .innerHTML),
    panel_template_warning_link = Handlebars.compile(template_element
                         .getElementById("panel-template-warning-link")
                         .innerHTML),
    panel_template_contextual_help = Handlebars.compile(template_element
                         .getElementById("panel-template-contextual-help")
                         .innerHTML);

  gadget_klass
    .setState({
      visible: false,
      desktop: false
    })
    //////////////////////////////////////////////
    // acquired method
    //////////////////////////////////////////////
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("translateHtml", "translateHtml")
    .declareAcquiredMethod("translate", "translate")
    .declareAcquiredMethod("renderEditorPanel", "renderEditorPanel")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("redirect", "redirect")

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

    .onStateChange(function (modification_dict) {
      var context = this,
        gadget = this,
        queue = new RSVP.Queue(),
        jio_key = modification_dict.jio_key,
        tmp_element;

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

      if (modification_dict.hasOwnProperty("global")) {
        queue
          .push(function () {
            return RSVP.all([
              context.getUrlFor({command: 'display', options: {page: "logout"}}),
              context.getUrlFor({command: 'display', options: {page: "search", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_site_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_ticket_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_invoice_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_service_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_computer_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_network_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_project_list", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_person_view", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slapos", editable: true}}),
              context.getUrlFor({command: 'display', options: {page: "slap_language_view"}})
            ]);
          })
          .push(function (result_list) {
            // XXX: Customize panel header!
            return context.translateHtml(
              panel_template_header() +
                panel_template_body({
                "logout_href": result_list[0],
                "search_href": result_list[1],
                "organisation_href": result_list[2],
                "support_request_href": result_list[3],
                "accounting_href": result_list[4],
                "hosting_subscription_href": result_list[5],
                "computer_href": result_list[6],
                "computer_network_href": result_list[7],
                "project_href": result_list[8],
                "person_href": result_list[9],
                "dashboard_href": result_list[10],
                "language_href": result_list[11]
              })
            );
          })
          .push(function (my_translated_or_plain_html) {
            tmp_element = document.createElement('div');
            tmp_element.innerHTML = my_translated_or_plain_html;
            return context.declareGadget('gadget_erp5_panel_shortcut.html', {
              scope: "gadget_erp5_panel_shortcut",
              element: tmp_element.querySelector('[data-gadget-scope="erp5_panel_shortcut"]')
            });
          })
          .push(function (panel_shortcut) {
            return panel_shortcut.render({
              focus: false
            });
          })
          .push(function () {
            context.element.querySelector("div").appendChild(tmp_element);
            return context.listenResize();
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
      if (this.element.querySelector('a[id="attention-point-link"]') === evt.target) {
        evt.preventDefault();
        return this.calculateMyAttentionPointList(this.state.jio_key, true);
      }
    }, false, false)

    .declareJob('listenResize', function () {
      // resize should be only trigger after the render method
      // as displaying the panel rely on external gadget (for translation for example)
      var result,
        event,
        context = this;
      function extractSizeAndDispatch() {
        if (window.matchMedia("(min-width: 90em)").matches) {
          return context.changeState({
            desktop: true
          });
        }
        return context.changeState({
          desktop: false
        });
      }
      result = loopEventListener(window, 'resize', false,
                                 extractSizeAndDispatch);
      event = document.createEvent("Event");
      event.initEvent('resize', true, true);
      window.dispatchEvent(event);
      return result;
    })

    .allowPublicAcquisition('notifyChange', function () {
      // Typing a search query should not modify the header status
      return;
    })

    .declareJob("calculateContextualHelpList", function (jio_key) {
      var context = this,
        queue = new RSVP.Queue(),
        contextual_help_dl = document.querySelector('dl.dl-contextual-help');
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
          if (contextual_help_list.length > 0) {
            if (!Boolean(document.querySelector('#contextual-help-link'))) {
              contextual_help_dl.innerHTML = panel_template_contextual_help({
                contextual_help_list: contextual_help_list
              })
              }
          }
        });
     })
    .declareJob("calculateMyAttentionPointList", function (jio_key, force_open) {
      var context = this,
        queue = new RSVP.Queue(),
        attention_point_ul = document.querySelector('ul.ul-attention-point'),
        seen_attention_point_dict = JSON.parse(window.sessionStorage.getItem('seen_attention_point_dict') || "{}");
      return queue
        .push(function () {
          return context.getSetting('hateoas_url');
        })
        .push(function (hateoas_url) {
          if (jio_key === false || jio_key === undefined || jio_key === null) {
            return [[], 'No Alert'];
          }
          return RSVP.all([context.jio_getAttachment(
            jio_key,
            hateoas_url + jio_key + '/Base_getAttentionPointList'
          ),
          context.translate('No Alert!')
          ]);
        })
        .push(function (result_list) {
          var attention_point_list = result_list[0],
            no_alert_caption = result_list[1];
          if (attention_point_list.length > 0) {
            if (!Boolean(document.querySelector('#attention-point-link'))) {
              attention_point_ul.innerHTML = panel_template_warning_link({
                amount: attention_point_list.length
              });
            }
            if (force_open || (JSON.stringify(seen_attention_point_dict[jio_key]) != JSON.stringify(attention_point_list))) {
              seen_attention_point_dict[jio_key] = attention_point_list;
              window.sessionStorage.setItem('seen_attention_point_dict', JSON.stringify(seen_attention_point_dict));
              return context.renderEditorPanel("gadget_erp5_attention_point.html", {
                attention_point_list: attention_point_list
              });
            }
          } else {
            attention_point_ul.innerHTML = "<li></li>";
            if (force_open) {
              return context.renderEditorPanel("gadget_erp5_attention_point.html", {
                attention_point_list: [[no_alert_caption, 'no-alert']]
              });
            }
          }
        });
    });

}(window, document, rJS, Handlebars, RSVP, Node, loopEventListener));
