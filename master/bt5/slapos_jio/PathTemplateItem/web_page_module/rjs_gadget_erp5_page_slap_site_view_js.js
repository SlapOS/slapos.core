/*global window, rJS, RSVP, JSON */
/*jslint nomen: true, indent: 2, maxerr: 3 */
(function (window, rJS, RSVP, JSON) {
  "use strict";

  rJS(window)
    /////////////////////////////////////////////////////////////////
    // Acquired methods
    /////////////////////////////////////////////////////////////////
    .declareAcquiredMethod("updateHeader", "updateHeader")
    .declareAcquiredMethod("updatePanel", "updatePanel")
    .declareAcquiredMethod("getUrlParameter", "getUrlParameter")
    .declareAcquiredMethod("getUrlFor", "getUrlFor")
    .declareAcquiredMethod("getSetting", "getSetting")
    .declareAcquiredMethod("updateDocument", "updateDocument")
    .declareAcquiredMethod("jio_getAttachment", "jio_getAttachment")
    .declareAcquiredMethod("jio_putAttachment", "jio_putAttachment")
    .declareAcquiredMethod("notifySubmitting", "notifySubmitting")
    .declareAcquiredMethod("notifySubmitted", 'notifySubmitted')
    .declareAcquiredMethod("jio_allDocs", "jio_allDocs")
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////

    .allowPublicAcquisition("jio_allDocs", function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0])
        .push(function (result) {
          var i, value, value_jio_key, len = result.data.total_rows;
          for (i = 0; i < len; i += 1) {
            if (result.data.rows[i].value.hasOwnProperty("getAccessStatus")) {
              value_jio_key = result.data.rows[i].id;
              value = result.data.rows[i].value.getAccessStatus;
              result.data.rows[i].value.getAccessStatus = {
                field_gadget_param : {
                  css_class: "",
                  description: gadget.description_translation,
                  hidden: 0,
                  default: "",
                  key: "status",
                  url: "gadget_slapos_status.html",
                  renderjs_extra: JSON.stringify({
                    jio_key: value_jio_key,
                    result: value
                  }),
                  title: gadget.title_translation,
                  type: "GadgetField"
                }
              };
              result.data.rows[i].value["listbox_uid:list"] = {
                key: "listbox_uid:list",
                value: 2713
              };
            }
          }
          return result;
        });
    })

    .declareMethod("render", function (options) {
      return this.changeState({
        jio_key: options.jio_key,
        doc: options.doc,
        editable: 1
      });
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
        .push(function (content) {
          return gadget.updateDocument(content);
        })
        .push(function () {
          return gadget.notifySubmitted({message: gadget.message_translation, status: 'success'});
        });
    })

    .declareMethod("triggerSubmit", function () {
      return this.element.querySelector('button[type="submit"]').click();
    })

    .onStateChange(function () {
      var gadget = this,
        page_title_translation,
        translation_list = [
          "Title",
          "Reference",
          "Latitude",
          "Longitude",
          "Monitoring",
          "Map",
          "Associated Servers",
          "Site",
          "The Status",
          "Status",
          "Data updated."
        ];
      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getDeclaredGadget('form_view'),
            gadget.getSetting("hateoas_url"),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          page_title_translation = result[2][7];
          gadget.description_translation = result[2][8];
          gadget.title_translation = result[2][9];
          gadget.message_translation = result[2][10];
          var editable = gadget.state.editable,
            column_list = [
              ['title', result[2][0]],
              ['reference', result[2][1]],
              ['getAccessStatus', result[2][9]]
            ];
          return result[0].render({
            erp5_document: {
              "_embedded": {"_view": {
                "my_title": {
                  "description": "",
                  "title": result[2][0],
                  "default": gadget.state.doc.title,
                  "css_class": "",
                  "required": 1,
                  "editable": editable,
                  "key": "title",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_reference": {
                  "description": "",
                  "title": result[2][1],
                  "default": gadget.state.doc.reference,
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "key": "reference",
                  "hidden": 0,
                  "type": "StringField"
                },
                "my_default_geographical_location_latitude": {
                  "description": "",
                  "title": result[2][2],
                  "default": gadget.state.doc.default_geographical_location_latitude,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "default_geographical_location_latitude",
                  "hidden": 0,
                  "type": "FloatField"
                },
                "my_default_geographical_location_longitude": {
                  "description": "",
                  "title": result[2][3],
                  "default": gadget.state.doc.default_geographical_location_longitude,
                  "css_class": "",
                  "required": 1,
                  "editable": 1,
                  "key": "default_geographical_location_longitude",
                  "hidden": 0,
                  "type": "FloatField"
                },
                "my_monitoring_status": {
                  "description": "",
                  "title": result[2][4],
                  "default": "",
                  "renderjs_extra": JSON.stringify({
                    jio_key: gadget.state.jio_key,
                    result: gadget.state.doc.news
                  }),
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_status.html",
                  "sandbox": "",
                  "key": "monitoring_status",
                  "hidden": 0,
                  "type": "GadgetField"
                },
                "my_organisation_map": {
                  "description": "",
                  "title": result[2][5],
                  "default": [
                    {"jio_key": gadget.state.jio_key,
                      "doc": {"title": gadget.state.doc.title,
                            "reference": gadget.state.doc.reference,
                            "result": gadget.state.doc.news,
                            "latitude": gadget.state.doc.default_geographical_location_latitude,
                            "longitude": gadget.state.doc.default_geographical_location_longitude}
                      }
                  ],
                  "css_class": "",
                  "required": 1,
                  "editable": 0,
                  "url": "gadget_slapos_compute_node_map.html",
                  "sandbox": "",
                  "key": "monitoring_status",
                  "hidden": 0,
                  "type": "GadgetField"
                },
                "listbox": {
                  "column_list": column_list,
                  "show_anchor": 0,
                  "default_params": {},
                  "editable": 0,
                  "editable_column_list": [],
                  "key": "slap_organisation_compute_node_listbox",
                  "lines": 10,
                  "list_method": "Organisation_getComputeNodeTrackingList",
                  "list_method_template": result[1] + "ERP5Document_getHateoas?mode=search&" +
                            "list_method=Organisation_getComputeNodeTrackingList&relative_url=" +
                            gadget.state.jio_key + "&default_param_json=eyJpZ25vcmVfdW5rbm93bl9jb2x1bW5zIjogdHJ1ZX0={&query,select_list*,limit*,sort_on*,local_roles*}",
                  "query": "urn:jio:allDocs?query=",
                  "portal_type": [],
                  "search_column_list": column_list,
                  "sort_column_list": column_list,
                  "sort": [["title", "ascending"]],
                  "title": result[2][6],
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
                "left",
                [["my_title"], ["my_reference"], ['my_monitoring_status'],
                  ["my_default_geographical_location_latitude"],
                  ["my_default_geographical_location_longitude"]]
              ], [
                "right",
                [['my_organisation_map']]
              ], [
                "bottom",
                [["listbox"]]
              ]]
            }
          });
        })
        .push(function () {
          return gadget.updatePanel({
            jio_key: "organisation_module"
          });
        })
        .push(function () {
          return RSVP.all([
            gadget.getUrlFor({command: "change", options: {editable: true}}),
            gadget.getUrlFor({command: 'history_previous'}),
            gadget.getUrlFor({command: "change", options: {page: "slap_delete_organisation"}})
          ]);
        })
        .push(function (url_list) {
          var header_dict = {
            selection_url: url_list[1],
            page_title: page_title_translation + " : " + gadget.state.doc.title,
            delete_url: url_list[2],
            save_action: true
          };
          if (!gadget.state.editable) {
            header_dict.edit_content = url_list[0];
          }
          return gadget.updateHeader(header_dict);
        });
    });
}(window, rJS, RSVP, JSON));