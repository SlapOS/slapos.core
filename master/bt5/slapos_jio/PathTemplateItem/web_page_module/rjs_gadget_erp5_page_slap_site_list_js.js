/*global window, rJS, RSVP */
/*jslint nomen: true, indent: 2, maxerr: 3*/
(function (window, rJS, RSVP) {
  'use strict';

  rJS(window)
    .declareAcquiredMethod('updateHeader', 'updateHeader')
    .declareAcquiredMethod('updatePanel', 'updatePanel')
    .declareAcquiredMethod('redirect', 'redirect')
    .declareAcquiredMethod('reload', 'reload')
    .declareAcquiredMethod('getSetting', 'getSetting')
    .declareAcquiredMethod('jio_get', 'jio_get')
    .declareAcquiredMethod('getUrlFor', 'getUrlFor')
    .declareAcquiredMethod('jio_allDocs', 'jio_allDocs')
    .declareAcquiredMethod('jio_getAttachment', 'jio_getAttachment')
    .declareAcquiredMethod('translate', 'translate')
    .declareAcquiredMethod("getTranslationList", "getTranslationList")

    .allowPublicAcquisition('jio_allDocs', function (param_list) {
      var gadget = this;
      return gadget.jio_allDocs(param_list[0]).push(function (result) {
        var i,
          value,
          value_jio_key,
          len = result.data.total_rows;
        for (i = 0; i < len; i += 1) {
          if (
            1 ||
              result.data.rows[i].value.hasOwnProperty('Organisation_getNewsDict')
          ) {
            value_jio_key = result.data.rows[i].id;
            value = result.data.rows[i].value.Organisation_getNewsDict;
            result.data.rows[i].value.Organisation_getNewsDict = {
              field_gadget_param: {
                css_class: '',
                description: 'The Status',
                hidden: 0,
                default: { jio_key: value_jio_key, result: value },
                key: 'status',
                url: 'gadget_slapos_status.html',
                title: 'Status',
                type: 'GadgetField'
              }
            };
            result.data.rows[i].value['listbox_uid:list'] = {
              key: 'listbox_uid:list',
              value: 2713
            };
          }
        }
        return result;
      });
    })

    /////////////////////////////////////////////////////////////////
    // declared methods
    /////////////////////////////////////////////////////////////////
    .declareMethod('triggerSubmit', function () {
      var argument_list = arguments;
      return this.getDeclaredGadget('form_list').push(function (gadget) {
        return gadget.triggerSubmit.apply(gadget, argument_list);
      });
    })
    .declareMethod('render', function () {
      var gadget = this,
        lines_limit,
        sites_translation,
        translation_list = [
          "Title",
          "Reference",
          "Region",
          "Status",
          "Sites"
        ];

      return new RSVP.Queue()
        .push(function () {
          return RSVP.all([
            gadget.getSetting('listbox_lines_limit', 20),
            window.getSettingMe(gadget)
          ]);
        })
        .push(function (settings) {
          lines_limit = settings[0];
          return RSVP.all([
            gadget.getDeclaredGadget('form_list'),
            gadget.jio_get(settings[1]),
            gadget.getTranslationList(translation_list)
          ]);
        })
        .push(function (result) {
          var i,
            destination_list,
            column_list = [
              ['title', result[2][0]],
              ['reference', result[2][1]],
              //['default_address_region_title', result[2][2]],
              ['Organisation_getNewsDict', result[2][3]]
            ];
          destination_list = '%22NULL%22%2C';
          sites_translation = result[2][4];
          for (i in result[1].assignment_destination_list) {
            if (result[1].assignment_destination_list.hasOwnProperty(i)) {
              destination_list +=
                '%22' + result[1].assignment_destination_list[i] + '%22%2C';
            }
          }
          return result[0].render({
            erp5_document: {
              _embedded: {
                _view: {
                  listbox: {
                    column_list: column_list,
                    show_anchor: 0,
                    default_params: {},
                    editable: 0,
                    editable_column_list: [],
                    key: 'slap_site_listbox',
                    lines: lines_limit,
                    list_method: 'portal_catalog',
                    query:
                      'urn:jio:allDocs?query=portal_type%3A%22' +
                      'Organisation' +
                      '%22%20AND%20role_title%3A%22Host%22%20AND%20' +
                      'relative_url%3A(' +
                      destination_list +
                      ')',
                    portal_type: [],
                    search_column_list: column_list,
                    sort_column_list: column_list,
                    sort: [['title', 'ascending']],
                    title: sites_translation,
                    type: 'ListBox'
                  }
                }
              },
              _links: {
                type: {
                  // form_list display portal_type in header
                  name: ''
                }
              }
            },
            form_definition: {
              group_list: [['bottom', [['listbox']]]]
            }
          });
        })
        .push(function () {
          return gadget.getSetting('frontpage_gadget');
        })
        .push(function (frontpage_gadget) {
          return RSVP.all([
            gadget.getUrlFor({
              command: 'change',
              options: { page: 'slap_add_organisation' }
            }),
            gadget.getUrlFor({ command: 'change', options: { page: frontpage_gadget}}),
            gadget.updatePanel({jio_key: 'organisation_module'})
          ]);
        })
        .push(function (result) {
          return gadget.updateHeader({
            page_title: sites_translation,
            selection_url: result[1],
            filter_action: true,
            add_url: result[0]
          });
        });
    });
}(window, rJS, RSVP));
