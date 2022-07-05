/*global document, window, rJS, RSVP, Chart, domsugar, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, domsugar, JSON) {
  "use strict";
  var gadget_klass = rJS(window);
  gadget_klass
    .ready(function (gadget) {
      gadget.property_dict = {};
      return gadget.getElement()
        .push(function (element) {
          gadget.property_dict.element = element;
          gadget.property_dict.deferred = RSVP.defer();
        });
    })
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")
    .declareAcquiredMethod("redirect", "redirect")
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("jio_get", "jio_get")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, value_jio_key, date, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("Organisation_getNewsDict")) {
              value_jio_key = result.data.rows[i].id;
              value = result.data.rows[i].value.Organisation_getNewsDict;
              result.data.rows[i].value.Organisation_getNewsDict = {
                field_gadget_param : {
                  css_class: "",
                  description: "The Status",
                  hidden: 0,
                  default: "",
                  renderjs_extra: JSON.stringify({
                    jio_key: value_jio_key,
                    result: value
                  }),
                  key: "status",
                  url: "gadget_slapos_status.html",
                  title: "Status",
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
            if (result.data.rows[i].value.hasOwnProperty("Event_getAcknowledgementDict")) {
              value_jio_key = result.data.rows[i].id;
              value = result.data.rows[i].value.Event_getAcknowledgementDict;
              result.data.rows[i].value.Event_getAcknowledgementDict = {
                field_gadget_param : {
                  editable: 1,
                  css_class: "",
                  description: "",
                  hidden: 0,
                  "default": value,
                  key: "acknowledge_message",
                  url: "gadget_slapos_alert_listbox_field.html",
                  title: "Acknowledge Message",
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
            if (result.data.rows[i].value.hasOwnProperty("modification_date")) {
              date = new Date(result.data.rows[i].value.modification_date);
              result.data.rows[i].value.modification_date = {
                allow_empty_time: 0,
                ampm_time_style: 0,
                css_class: "date_field",
                date_only: 0,
                description: "The Date",
                editable: 0,
                hidden: 0,
                hidden_day_is_last_day: 0,
                "default": date.toUTCString(),
                key: "modification_date",
                required: 0,
                timezone_style: 0,
                title: "Modification Date",
                type: "DateTimeField"
              };
            }
          }
          return result;
        });
    })

    .allowPublicAcquisition("updateHeader", function () {
      return;
    })

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod("render", function () {
      var gadget = this,
        translation_list = [
          "Title",
          "Status",
          "Sites"
        ];
      return new RSVP.Queue()
        .push(function () {
          var lines_limit;

          return new RSVP.Queue()
            .push(function () {
              return RSVP.all([
                gadget.getSetting("listbox_lines_limit", 100),
                window.getSettingMe(gadget),
                gadget.jio_getAttachment('acl_users', 'links')
              ]);
            })
            .push(function (settings) {
              lines_limit = settings[0];
              return RSVP.all([
                gadget.getDeclaredGadget('right'),
                gadget.jio_get(settings[1]),
                gadget.getTranslationList(translation_list)
              ]);
            })
            .push(function (result) {
              var i, destination_list, column_list = [
                ['title', result[2][0]],
                ['Organisation_getNewsDict', result[2][1]]
              ];
              gadget.me_dict = result[1];
              destination_list = "%22NULL%22%2C";
              for (i in result[1].assignment_destination_list) {
                if (result[1].assignment_destination_list.hasOwnProperty(i)) {
                  destination_list += "%22" + result[1].assignment_destination_list[i] + "%22%2C";
                }
              }
              return result[0].render({
                erp5_document: {
                  "_embedded": {"_view": {
                    "listbox": {
                      "column_list": column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 0,
                      "editable_column_list": [],
                      "key": "slap_site_listbox",
                      "lines": lines_limit,
                      "list_method": "portal_catalog",
                      "query": "urn:jio:allDocs?query=portal_type%3A%22" +
                        "Organisation" + "%22%20AND%20role_title%3A%22Host%22%20AND%20" +
                        "relative_url%3A(" + destination_list + ")",
                      "portal_type": [],
                      "search_column_list": column_list,
                      "sort_column_list": column_list,
                      "sort": [["title", "ascending"]],
                      "title": result[2][2],
                      "type": "ListBox"
                    }
                  }},
                  "_links": {
                    "type": {
                      // form_list display portal_type in header
                      name: ""
                    }
                  }
                },
                form_definition: {
                  group_list: [[
                    "bottom",
                    [["listbox"]]
                  ]]
                }
              });
            });
        })
        .push(function () {
          return new RSVP.Queue()
            .push(function () {
              return RSVP.all([
                gadget.getDeclaredGadget('top'),
                gadget.getSetting("hateoas_url")
              ]);
            })
            .push(function (result) {
              var column_list = [
                ['Event_getAcknowledgementDict', ' ']
              ];

              return result[0].render({
                erp5_document: {
                  "_embedded": {"_view": {
                    "listbox": {
                      "column_list": column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      editable: 1,
                      "editable_column_list": column_list,
                      "key": "slap_acknowledgement_listbox",
                      "lines": 5,
                      "list_method": "AcknowledgementTool_getUserUnreadAcknowledgementValueList",
                      "list_method_template": result[1] + "ERP5Document_getHateoas?mode=search&" +
                        "list_method=AcknowledgementTool_getUserUnreadAcknowledgementValueList" +
                        "{&query,select_list*,limit*,sort_on*,local_roles*}",
                      "query": "urn:jio:allDocs?query=",
                      "portal_type": [],
                      "search_column_list": column_list,
                      "sort_column_list": column_list,
                      "sort": [["Event_getAcknowledgementDict", "ASC"]],
                      "title": "Notifications",
                      "type": "ListBox"
                    }
                  }},
                  "_links": {
                    "type": {
                      // form_list display portal_type in header
                      name: ""
                    }
                  }
                },
                form_definition: {
                  group_list: [[
                    "bottom",
                    [["listbox"]]
                  ]]
                }
              });
            });
        })
        .push(function () {
          var lines_limit = 15,
            translation_list1 = [
              "Title",
              "Modification Date",
              "State",
              "Pending Tickets to Process",
              "Dashboard",
              "Show All Tickets",
              "RSS"
            ];
          return new RSVP.Queue()
            .push(function () {
              return RSVP.all([
                gadget.getDeclaredGadget('last'),
                gadget.getTranslationList(translation_list1),
                gadget.getUrlFor({command: 'change', options: {page: "slap_ticket_list"}}),
                gadget.getUrlFor({command: 'change', options: {page: "slap_rss_ticket"}})
              ]);
            })
            .push(function (result) {
              gadget.page_title_translation = result[1][4];
              var form_list = result[0],
                bottom_header = domsugar('div', {"class": "slapos-control-front"},
                  [
                    domsugar("center", {}, [
                      domsugar("a",
                        {"class": "ui-btn ui-first-child ui-btn-white-front  ui-btn-icon-left ui-icon-sort-alpha-asc",
                          "text": result[1][5],
                          "href": result[2]}),
                      domsugar("a",
                        {"class": "ui-btn ui-first-child ui-btn-white-front  ui-btn-icon-left ui-icon-rss",
                          "text": result[1][6],
                          "href": result[3]})
                    ])
                  ]),
                div_bottom_header = gadget.element.querySelector(".box-gadget-bottom-header"),
                column_list = [
                  ['title', result[1][0]],
                  ['modification_date', result[1][1]],
                  ['translated_simulation_state_title', result[1][2]]
                ];
              div_bottom_header.appendChild(bottom_header);
              return form_list.render({
                erp5_document: {
                  "_embedded": {"_view": {
                    "listbox": {
                      "column_list": column_list,
                      "show_anchor": 0,
                      "default_params": {},
                      "editable": 0,
                      "editable_column_list": [],
                      "key": "slap_ticket_listbox",
                      "lines": lines_limit,
                      "list_method": "portal_catalog",
                      "query": "urn:jio:allDocs?query=portal_type%3A%20%28%22Support%20Request%22%2C%20%22Upgrade%20Decision%22%2C%20%22Regularisation%20Request%22%29%20AND%20" +
                        "destination_decision_reference%3A" +  gadget.me_dict.reference + "%20AND%20simulation_state%3A%20%28%22suspended%22%2C%20%22confirmed%22%29",
                      "portal_type": [],
                      "search_column_list": column_list,
                      "sort_column_list": column_list,
                      "sort": [["modification_date", "Descending"]],
                      "title": result[1][3],
                      "type": "ListBox"
                    }
                  }},
                  "_links": {
                    "type": {
                      // form_list display portal_type in header
                      name: ""
                    }
                  }
                },
                form_definition: {
                  group_list: [[
                    "bottom",
                    [["control"], ["listbox"]]
                  ]]
                }
              });
            });
        })
        .push(function () {
          return gadget.getSetting('frontpage_gadget');
        })
        .push(function (frontpage_gadget) {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {"page": frontpage_gadget}}),
            gadget.updatePanel({jio_key: false})
          ]);
        })
        .push(function (url_list) {
          return gadget.updateHeader({
            page_title: gadget.page_title_translation,
            selection_url: url_list[0]
          });
        });
    })
    .declareService(function () {
      var destination_list, gadget = this;
      return window.getSettingMe(gadget)
        .push(function (me) {
          return gadget.jio_get(me);
        })
        .push(function (person_doc) {
          var i;
          destination_list = '"NULL"';
          for (i in person_doc.assignment_destination_list) {
            if (person_doc.assignment_destination_list.hasOwnProperty(i)) {
              destination_list += ' ,"' + person_doc.assignment_destination_list[i] + '"';
            }
          }
          return gadget.jio_allDocs({
            query: "portal_type:Organisation AND role_title:Host AND relative_url:(" + destination_list + ")",
            select_list: ['title',
                          'reference',
                          'Organisation_getNewsDict',
                          'default_geographical_location_longitude',
                          'default_geographical_location_latitude']
          });
        })
        .push(function (result) {
          var idx, marker_list = [];
          for (idx in result.data.rows) {
            if (result.data.rows.hasOwnProperty(idx)) {
              marker_list.push({
                "jio_key": result.data.rows[idx].id,
                "doc": {"title": result.data.rows[idx].value.title,
                        "reference": result.data.rows[idx].value.reference,
                        "result": result.data.rows[idx].value.Organisation_getNewsDict,
                        "latitude": result.data.rows[idx].value.default_geographical_location_latitude,
                        "longitude": result.data.rows[idx].value.default_geographical_location_longitude}
              });
            }
          }
          return gadget.getElement()
            .push(function (element) {
              return gadget.declareGadget("gadget_erp5_page_map.html", {
                scope: "map",
                element: element.querySelector(".map-gadget")
              });
            })
            .push(function (map_gadget) {
              var map_options = {
                zoom : 40,
                marker_list : marker_list
              };
              if (marker_list.length === 0) {
                map_options.doc = {
                  latitude: 48.858370,
                  longitude: 2.294481
                };
                map_options.zoom = 10;
              }
              return map_gadget.render(map_options);
            });
        });
    });
}(window, rJS, RSVP, domsugar, JSON));