/*jslint indent: 2, maxerr: 3, nomen: true */
/*global window, document, rJS, RSVP, domsugar*/
(function (window, document, rJS, RSVP, domsugar) {
  "use strict";

  function createAttentionPointItem(item_list) {
    var i, attention_point_item = [];
    for (i in item_list) {
      if (item_list.hasOwnProperty(i)) {
        if (item_list[i].link) {
          attention_point_item.push(
            domsugar("div", {class: "attention-point"}, [
              domsugar("a", {
                href: item_list[i].link,
                text: item_list[i].text
              })
            ])
          );
        } else {
          attention_point_item.push(
            domsugar("div", {
              class: "attention-point",
              text: item_list[i].text
            })
          );
        }
      }
    }
    return attention_point_item;
  }

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
          return createAttentionPointItem([
            {
              text: attention_point.text,
              link: link
            }]);
        });
    }
    return createAttentionPointItem([
      {
        text: attention_point.text,
        link: attention_point.link
      }]);
  }

  function createAttentionPointHeader(container) {
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    return domsugar(container, {
      class: "ui-header ui-bar-inherit attention_point_header",
      "data-role": "header",
      role: "banner"
    }, [
      domsugar("div", {class: "ui-controlgroup ui-controlgroup-horizontal ui-btn-right"}, [
        domsugar("div", {class: "ui-controlgroup-controls"})
      ]),
      domsugar('h1', {class: "ui-title", role: "heading", "aria-level": "1", text: "Warnings" }),
      domsugar("div", {class: "ui-controlgroup ui-controlgroup-horizontal ui-btn-left"}, [
        domsugar("div", {class: "ui-controlgroup-controls"}, [
          domsugar("button", {
            text: "Close",
            type: "submit",
            "data-rel": "save",
            class: "close responsive ui-first-child ui-btn ui-btn-icon-left ui-icon-times"
          })])
      ])
    ]);
  }
  rJS(window)
    //////////////////////////////////////////////
    // acquired method
    //////////////////////////////////////////////
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("trigger", "trigger")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .onStateChange(function onStateChange() {
      var gadget = this,
        container = gadget.element.querySelector(".attention_point_header");
      createAttentionPointHeader(container);
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all(gadget.state.attention_point_list
            .map(function (attention_point) {
              return createAttentionPointTemplate(gadget, attention_point);
            }));
        })
        .push(function (result_list) {
          var i,
            attention_point_item_container = gadget.element.querySelector('.attention_point_item_container');
          for (i = 0; i < result_list.length; i += 1) {
            attention_point_item_container.appendChild(
              domsugar("div", {}, [result_list[i]])
            );
          }
          return createAttentionPointHeader(container);          
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
}(window, document, rJS, RSVP, domsugar));