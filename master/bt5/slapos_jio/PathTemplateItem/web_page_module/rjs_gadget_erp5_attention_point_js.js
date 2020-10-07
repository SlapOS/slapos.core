/*jslint indent: 2, maxerr: 3, nomen: true */
/*global window, document, rJS, RSVP, Handlebars*/
(function (window, document, rJS, RSVP, Handlebars) {
  "use strict";
  var gadget_klass = rJS(window),
    template_element = gadget_klass.__template_element,
    attention_point_item_template = Handlebars.compile(template_element
                         .getElementById("attention_point-item-template")
                         .innerHTML),
    attention_point_template = Handlebars.compile(template_element
                         .getElementById("attention_point-template")
                         .innerHTML);
  Handlebars.registerHelper('equal', function (left_value, right_value, options) {
    if (arguments.length < 3) {
      throw new Error("Handlebars Helper equal needs 2 parameters");
    }
    if (left_value !== right_value) {
      return options.inverse(this);
    }
    return options.fn(this);
  });

  function createAttentionPointTemplate(gadget, attention_point) {
    var page = "slap_controller", option_dict = {};
    if (attention_point.link || attention_point.page) {
      if (attention_point.page) {
        page = attention_point.page;
      }
      option_dict.page = page;
      if (attention_point.link) {
        option_dict.jio_key = attention_point.link;
      }
      return gadget.getUrlFor({command: 'change', options: option_dict})
        .push(function (link) {
          return gadget.translateHtml(attention_point_item_template({
            option: [{
              text: attention_point.text,
              link: link
            }]
          }));
        });
    }
    return gadget.translateHtml(attention_point_item_template({
      option: [{
        text: attention_point.text,
        link: attention_point.link
      }]
    }));
  }
  gadget_klass
    //////////////////////////////////////////////
    // acquired method
    //////////////////////////////////////////////
    .declareAcquiredMethod("translateHtml", "translateHtml")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("trigger", "trigger")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .onStateChange(function onStateChange() {
      var gadget = this,
        div = document.createElement("div"),
        container = gadget.element.querySelector(".container");
      return gadget.translateHtml(attention_point_template())
        .push(function (translated_html) {
          div.innerHTML = translated_html;
          return RSVP.all(gadget.state.attention_point_list
            .map(function (attention_point) {
              return createAttentionPointTemplate(gadget, attention_point);
            })
            );
        })
        .push(function (result_list) {
          var i,
            subdiv,
            attention_point_item_container = div.querySelector('.attention_point_item_container');
          for (i = 0; i < result_list.length; i += 1) {
            subdiv = document.createElement("div");
            subdiv.innerHTML = result_list[i];
            attention_point_item_container.appendChild(subdiv);
          }
          while (container.firstChild) {
            container.removeChild(container.firstChild);
          }
          container.appendChild(div);
        });
    })
    .declareMethod('render', function render(options) {
      return this.changeState({
        attention_point_list: options.attention_point_list || [],
        key: options.key
      });
    })
    .onEvent('click', function click(evt) {
      if (evt.target.classList.contains('close')) {
        evt.preventDefault();
        return this.trigger();
      }
    }, false, false)
    .onEvent('submit', function submit() {
      var gadget = this,
        sort_list = gadget.element.querySelectorAll(".attention_point_item_container"),
        sort_query = [],
        select_list,
        sort_item,
        options = {},
        i;
      for (i = 0; i < sort_list.length; i += 1) {
        sort_item = sort_list[i];
        select_list = sort_item.querySelectorAll("select");
        sort_query[i] = [select_list[0][select_list[0].selectedIndex].value,
          select_list[1][select_list[1].selectedIndex].value];
      }
      if (i === 0) {
        options[gadget.state.key] = undefined;
      } else {
        options[gadget.state.key] = sort_query;
      }
      return gadget.redirect({
        command: 'store_and_change',
        options: options
      });
    });
}(window, document, rJS, RSVP, Handlebars));