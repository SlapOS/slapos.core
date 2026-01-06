/*globals window, document, RSVP, rJS, XMLHttpRequest, URL,
          jIO, domsugar, XMLSerializer */
/*jslint indent: 2, maxlen: 200*/
(function (window, document, RSVP, rJS, XMLHttpRequest, URL,
           jIO, domsugar, XMLSerializer) {
  "use strict";

  //////////////////////////////////////////////////////
  // globals
  //////////////////////////////////////////////////////
  var page_container,
    BROKEN_JSON_URL = 'http://0.0.0.0',
    DISPLAY_INSTANCE_TREE_LIST = 'display_instance_tree_list',
    DISPLAY_INSTANCE_TREE = 'display_instance_tree',
    DISPLAY_INSTANCE_TREE_UPDATE_DIALOG = 'display_instance_tree_update_dialog',
    SEARCH_CONNECTION_PARAMETER = 'search_connection_parameter',
    DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG = 'display_select_software_release_request_dialog',
    DISPLAY_REQUEST_DIALOG = 'display_request_dialog';

  //////////////////////////////////////////////////////
  // Helpers
  //////////////////////////////////////////////////////
  function callJsonRpcEntryPoint(url, data) {
    if (data === undefined) {
      data = {};
    }
    return RSVP.Queue(jIO.util.ajax({
      // use relative path in case we are behind a proxy
      // panel is at panel/ path and slaptool is at the "top"
      url: '..' + url,
      type: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json'
      },
      dataType: 'json',
      data: JSON.stringify(data)
    }))
      .push(function (evt) {
        return evt.target.response;
      });
  }

/*
  function callHateoasEntryPoint(url_template_string, options) {
    if (options === undefined) {
      options = {};
    }
    var url_template = UriTemplate.parse(url_template_string);

    return RSVP.Queue(jIO.util.ajax({
      url: url_template.expand(options),
      type: 'GET',
      headers: {
        Accept: 'application/json'
      },
      dataType: 'json'
    }))
      .push(function (evt) {
        return evt.target.response;
      });
  }
*/

  function returnUrlIfPresent(url) {
    return RSVP.Queue(jIO.util.ajax({
      url: url,
      type: 'HEAD'
    }))
      .push(function () {
        return url;
      }, function (evt) {
        if ((evt.target.status === 404) || (evt.target.status === 403)) {
          return null;
        }
        throw evt;
      });
  }

  function guessSoftwareReleaseJsonUrl(software_release_uri) {
    var json_url,
      promise_list = [],
      index;
    // First, consider the json location is by default:
    // software_release_uri + .json
    try {
      // Prevent calling an local url, which will be relative to the panel url
      json_url = new URL(software_release_uri + '.json',
                         software_release_uri).href;
    } catch (error) {
      // Return an url which will always fail
      // to force the gadget to render the textarea
      json_url = BROKEN_JSON_URL;
    }

    // Then, check if the panel has a public directory,
    // that can be used to provide a local json + schema
    // Try the known lab.nexedi.com url pattern
    index = software_release_uri.indexOf('/software/');
    if (index !== -1) {
      promise_list.push(returnUrlIfPresent(
        './public' + software_release_uri.slice(index) + '.json'
      ));
    }
    promise_list.push(json_url);

    return new RSVP.Queue(RSVP.all(promise_list))
      .push(function (result_list) {
        // Return the first result found
        var i,
          len = result_list.length;
        for (i = 0; i < len; i += 1) {
          if (result_list[i]) {
            return result_list[i];
          }
        }
      });
  }

  function getTranslationDict() {
    var word_list = ['Services', 'Instance Tree', 'Request'];
    // return gadget.getTranslationList(word_list)
    return new RSVP.Queue(word_list)
      .push(function (result_list) {
        var result = {},
          i;
        for (i = 0; i < word_list.length; i += 1) {
          result[word_list[i]] = result_list[i];
        }
        return result;
      });
  }

  //////////////////////////////////////////////////////
  // Header
  //////////////////////////////////////////////////////
  function renderGadgetHeader(gadget, loading, translation_dict, extra_dict) {
    var klass,
      attribute_dict = {},
      text,
      dataset,
      element,
      element_list = [],
      container = gadget.element.querySelector('a#slapproxy_header_title');

    if (loading) {
      klass = 'ui-icon-spinner';
      // Keep the previous text while loading
      text = container.textContent;
    } else {

      if (gadget.state.display_step === DISPLAY_INSTANCE_TREE_LIST) {
        klass = 'ui-icon-home';
        text = 'Services';
      } else if (gadget.state.display_step === DISPLAY_INSTANCE_TREE) {
        klass = 'ui-icon-arrow-up';
        text = 'Instance Tree';
        dataset = {
          'data-display_step': DISPLAY_INSTANCE_TREE_LIST
        };
      } else if (gadget.state.display_step === DISPLAY_INSTANCE_TREE_UPDATE_DIALOG) {
        klass = 'ui-icon-times';
        text = 'Instance Tree';
        dataset = {
          'data-display_step': DISPLAY_INSTANCE_TREE,
          'data-instance_guid': gadget.state.instance_guid
        };
      } else if ((gadget.state.display_step === DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG) ||
                 (gadget.state.display_step === DISPLAY_REQUEST_DIALOG)) {
        klass = 'ui-icon-plus';
        text = 'Request';
        dataset = {
          'data-display_step': DISPLAY_INSTANCE_TREE_LIST
        };
      } else {
        throw new Error("Can't render header state " +
                        gadget.state.display_step);
      }

      text = translation_dict[text];
      if (extra_dict) {
        if (extra_dict.title) {
          text = text + ': ' + extra_dict.title;
        }
      }
    }

    attribute_dict = {
      'class': 'ui-btn-icon-left ' + klass
    };

    if (dataset) {
      dataset.type = 'button';
      dataset.text = text;
      element = domsugar('button', dataset);
      // fix the CSS rendering
      element.style.display = 'unset';
      element_list.push(element);
    } else {
      attribute_dict.text = text;
    }

    domsugar(container, attribute_dict, element_list);
  }


  //////////////////////////////////////////////////////
  // DISPLAY_INSTANCE_TREE_LIST
  //////////////////////////////////////////////////////
  function renderInstanceTreeList(gadget, translation_dict) {

    return callJsonRpcEntryPoint('/slapos.allDocs.WIP.instance_tree_list')
      .push(function (json_response) {
        var instance_tree_list = json_response.result_list,
          element_list = [],
          i;

        for (i = 0; i < instance_tree_list.length; i += 1) {
          element_list.push(domsugar('li', [
            domsugar('a', {}, [
              domsugar('button', {
                type: 'button',
                text: instance_tree_list[i].title,
                'data-display_step': DISPLAY_INSTANCE_TREE,
                'data-instance_guid': instance_tree_list[i].instance_guid
              })
            ])
          ]));
        }

        domsugar(page_container, [
          domsugar('button', {
            type: 'button',
            // XXX TODO move to the left panel
            text: "Request",
            'data-display_step': DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG,
            'class': 'ui-btn-icon-left ui-icon-plus'
          }),
          domsugar('section', {'class': 'document_list'}, [
            domsugar('ul', {'class': 'document-listview'}, element_list)
          ])
        ]);
        renderGadgetHeader(gadget, false, translation_dict);
      });
  }

  //////////////////////////////////////////////////////
  // DISPLAY_INSTANCE_TREE
  //////////////////////////////////////////////////////
  function renderInstanceTree(gadget, translation_dict) {
    var json_response,
      form_view_gadget;

    return new RSVP.Queue(RSVP.hash({
      form_view_gadget: gadget.declareGadget('external/gadget_erp5_form.html'),
      json_response: callJsonRpcEntryPoint(
        '/slapos.get.v0.software_instance',
        {
          instance_guid: gadget.state.instance_guid
        }
      )
    }))
      .push(function (hash) {
        json_response = hash.json_response;
        form_view_gadget = hash.form_view_gadget;

        return form_view_gadget.render({
          erp5_document: {
            "_embedded": {"_view": {
              "my_title": {
                "title": "Title",
                "default": json_response.title,
                "required": 1,
                "editable": 0,
                "key": "title",
                "hidden": 0,
                "type": "StringField"
              },
              "my_software_type": {
                "title": "Software Type",
                "default": json_response.software_type,
                "required": 1,
                "editable": 0,
                "key": "software_type",
                "hidden": 0,
                "type": "StringField"
              },
              "my_software_release_uri": {
                "title": "Software Release",
                "default": json_response.software_release_uri,
                "required": 1,
                "editable": 0,
                "key": "software_release_uri",
                "hidden": 0,
                "type": "StringField"
              },
              "my_state": {
                "title": "State",
                "default": json_response.state,
                "required": 1,
                "editable": 0,
                "key": "state",
                "hidden": 0,
                "type": "StringField"
              },
              "edit_button": {
                "title": "",
                "default": domsugar('button', {
                  type: 'button',
                  // XXX TODO move to the left panel
                  text: "Update Parameter",
                  'data-display_step': DISPLAY_INSTANCE_TREE_UPDATE_DIALOG,
                  'data-instance_guid': json_response.instance_guid,
                  'class': 'ui-btn-icon-left ui-icon-sliders'
                }).outerHTML,
                "required": 1,
                "editable": 0,
                "key": "edit_button",
                "hidden": 0,
                "type": "EditorField"
              },
              "connection_listbox": {
                "sort": [],
                "show_stat": false,
                "domain_root_list": [],
                "search_column_list": [],
                "description": "",
                "portal_type": [],
                "editable": 0,
                "checked_uid_list": [],
                "show_select": 1,
                "key": "field_connection_listbox",
                "query": "urn:jio:allDocs?query=" + SEARCH_CONNECTION_PARAMETER,
                "default_params": {
                  "ignore_unknown_columns": true
                },
                "editable_column_list": [],
                "title": "Connection Parameters",
                "css_class": "",
                "show_anchor": 0,
                "lines": 200,
                "all_column_list": [],
                "autocomplete": null,
                "sort_column_list": [],
                "column_list": [
                  [
                    "connection_key",
                    "Parameter"
                  ],
                  [
                    "connection_value",
                    "Value"
                  ]
                ],
                "selection_name": "instance_tree_connection_hateoas_selection",
                "show_count": false,
                "domain_dict": {},
                "hidden": 0,
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
              "left", [["my_title"], ["my_software_type"], ["my_software_release_uri"]]
            ], [
              "right", [["my_state"], ["edit_button"]]
            ], [
              "bottom", [["connection_listbox"]]
            ]]
          }
        });
      })
      .push(function () {
        domsugar(page_container, [form_view_gadget.element]);
        renderGadgetHeader(gadget, false, translation_dict, {
          title: json_response.title
        });
      });
  }

  function searchConnectionParameterList(gadget) {
    return callJsonRpcEntryPoint(
      '/slapos.get.v0.software_instance',
      {
        instance_guid: gadget.state.instance_guid
      }
    )
      .push(function (json_response) {
        var connection_dict = json_response.connection_parameters,
          result_list = [],
          key;

        if (connection_dict.hasOwnProperty("_")) {
          connection_dict = JSON.parse(connection_dict["_"]);
        }

        for (key in connection_dict) {
          if (connection_dict.hasOwnProperty(key)) {
            result_list.push({
              connection_key: {
                "url_value": {},
                "field_gadget_param": {
                  "description": "",
                  "title": "Connection Key",
                  "default": key,
                  "css_class": "",
                  "required": null,
                  "editable": false,
                  "autocomplete": null,
                  "url": "gadget_slapos_label_listbox_field.html",
                  "sandbox": "",
                  "renderjs_extra": "{}",
                  "key": "field_connection_listbox_connection_key_" + connection_dict[key],
                  "hidden": 0,
                  "type": "GadgetField"
                }
              },
              "connection_value": {
                "url_value": {},
                "field_gadget_param": {
                  "description": "",
                  "title": "Connection Value",
                  "default": connection_dict[key],
                  "css_class": "",
                  "required": null,
                  "editable": false,
                  "autocomplete": null,
                  "url": "gadget_slapos_label_listbox_field.html",
                  "sandbox": "",
                  "renderjs_extra": "{}",
                  "key": "field_connection_listbox_connection_value_" + connection_dict[key],
                  "hidden": 0,
                  "type": "GadgetField"
                }
              }
            });
          }
        }

        return result_list;
      });
  }

  //////////////////////////////////////////////////////
  // DISPLAY_INSTANCE_TREE_UPDATE_DIALOG
  //////////////////////////////////////////////////////
  function renderInstanceTreeUpdateDialog(gadget, translation_dict) {
    var json_response,
      form_dialog_gadget;

    return new RSVP.Queue(RSVP.hash({
      form_dialog_gadget: gadget.declareGadget('external/gadget_erp5_pt_form_dialog.html'),
      json_response: callJsonRpcEntryPoint(
        '/slapos.get.v0.software_instance',
        {
          instance_guid: gadget.state.instance_guid
        }
      )
    }))
      .push(function (hash) {
        json_response = hash.json_response;
        form_dialog_gadget = hash.form_dialog_gadget;

        // Assert, as JSON api in slapproxy only support the top instance
        if (json_response.title !== json_response.root_instance_title) {
          throw new Error('Only the top instance is supported');
        }

        return guessSoftwareReleaseJsonUrl(json_response.software_release_uri);
      })
      .push(function (json_url) {

        var xml_document = document.implementation.createDocument(
          null,
          'instance'
        ),
          key,
          xml_element,
          parameter_xml;

        // Convert the json parameter to xml
        for (key in json_response.parameters) {
          if (json_response.parameters.hasOwnProperty(key)) {
            xml_element = xml_document.createElement('parameter');
            xml_element.setAttribute('id', String(key));
            xml_element.textContent = String(json_response.parameters[key]);
            xml_document.firstElementChild.appendChild(xml_element);
          }
        }
        parameter_xml = '<?xml version="1.0" encoding="UTF-8"?>' +
          (new XMLSerializer()).serializeToString(xml_document);

        return form_dialog_gadget.render({
          erp5_document: {
            "_embedded": {"_view": {
              // _actions is needed for form_dialog compatibility
              "_actions": {
                "put": "."
              },
              "your_instance_xml": {
                "title": "Instance Parameter",
                "url": "gadget_erp5_page_slap_parameter_form.html",
                "default": "",
                "renderjs_extra": JSON.stringify({
                  json_url: json_url,
                  shared: json_response.shared,
                  softwaretype: json_response.software_type,
                  parameter_xml: parameter_xml,
                  restricted_softwaretype: true
                }),
                "required": 1,
                "editable": 1,
                "key": "title",
                "hidden": 0,
                "type": "GadgetField"
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
            title: "Update Parameters",
            action: true,
            group_list: [[
              "center", [["your_instance_xml"]]
            ]]
          }
        });
      })
      .push(function () {
        domsugar(page_container, [form_dialog_gadget.element]);
        renderGadgetHeader(gadget, false, translation_dict, {
          title: json_response.title
        });
      });
  }

  function submitInstanceTreeUpdateDialog(gadget, translation_dict, data) {
    return callJsonRpcEntryPoint(
      '/slapos.get.v0.software_instance',
      {
        instance_guid: gadget.state.instance_guid
      }
    )
      .push(function (json_response) {
        var xml_document = rJS.parseDocumentStringOrFail(
          data.text_content,
          "application/xml"
        ),
          i,
          parameter_list,
          len,
          json_document = {};

        // Convert the parameter_xml to json
        parameter_list = xml_document.getElementsByTagName("parameter");
        len = parameter_list.length;
        for (i = 0; i < len; i += 1) {
          json_document[parameter_list[i].getAttribute("id")] = parameter_list[i].textContent;
        }

        return callJsonRpcEntryPoint('/slapos.post.v0.software_instance', {
          title: json_response.title,
          software_release_uri: json_response.software_release_uri,
          software_type: data.software_type,
          shared: json_response.shared,
          state: json_response.state,
          parameters: json_document,
          sla_parameters: json_response.sla_parameters
        });
      })
      .push(function () {
        return gadget.redirectChangeState({
          display_step: DISPLAY_INSTANCE_TREE
        });
      });
  }

  //////////////////////////////////////////////////////
  // DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG
  //////////////////////////////////////////////////////
  function renderSelectSoftwareReleaseRequestDialog(gadget, translation_dict) {
    var form_dialog_gadget;
    // First, get the list of computers
    return new RSVP.Queue(callJsonRpcEntryPoint(
      '/slapos.allDocs.WIP.compute_node_list',
      {}
    ))
      .push(function (json_response) {
        // Then, get the list of installed software release
        var promise_list = [],
          i;
        for (i = 0; i < json_response.result_list.length; i += 1) {
          promise_list.push(callJsonRpcEntryPoint(
            '/slapos.allDocs.v0.compute_node_software_installation_list',
            {
              'computer_guid': json_response.result_list[i].computer_guid
            }
          ));
        }

        return RSVP.hash({
          form_dialog_gadget: gadget.declareGadget('external/gadget_erp5_pt_form_dialog.html'),
          software_installation_list_list: RSVP.all(promise_list)
        });
      })
      .push(function (hash) {
        var software_installation_list_list = hash.software_installation_list_list,
          software_installation_item_list = [],
          software_release,
          i,
          j;
        form_dialog_gadget = hash.form_dialog_gadget;
        for (i = 0; i < software_installation_list_list.length; i += 1) {
          for (j = 0; j < software_installation_list_list[i].result_list.length; j += 1) {
            software_release = software_installation_list_list[i].result_list[j].software_release_uri;
            software_installation_item_list.push([
              software_release,
              software_release
            ]);
          }
        }
        software_installation_item_list.sort();

        return form_dialog_gadget.render({
          erp5_document: {
            "_embedded": {"_view": {
              // _actions is needed for form_dialog compatibility
              "_actions": {
                "put": "."
              },
              "your_url_string": {
                "description": "",
                "title": "Software Release",
                "default": "",
                "css_class": "",
                "select_first_item": 0,
                "required": 1,
                "editable": 1,
                "autocomplete": null,
                "key": "url_string",
                "items": software_installation_item_list,
                "hidden": 0,
                "type": "RadioField",
                "orientation": "vertical"
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
            title: "Request",
            action: true,
            group_list: [[
              "left", [["your_url_string"]]
            ]]
          }
        });
      })
      .push(function () {
        domsugar(page_container, [form_dialog_gadget.element]);
        renderGadgetHeader(gadget, false, translation_dict, {});

      });
  }

  function submitSelectSoftwareReleaseRequestDialog(gadget, translation_dict, data) {
    return gadget.redirectChangeState({
      display_step: DISPLAY_REQUEST_DIALOG,
      software_release_uri: data.url_string
    });
  }

  //////////////////////////////////////////////////////
  // DISPLAY_REQUEST_DIALOG
  //////////////////////////////////////////////////////
  function renderRequestDialog(gadget, translation_dict) {
    var form_dialog_gadget;

    return new RSVP.Queue(RSVP.hash({
      form_dialog_gadget: gadget.declareGadget('external/gadget_erp5_pt_form_dialog.html'),
      json_url: guessSoftwareReleaseJsonUrl(gadget.state.software_release_uri)
    }))
      .push(function (hash) {
        var json_url = hash.json_url,
          xml_document = document.implementation.createDocument(
            null,
            'instance'
          ),
          parameter_xml;
        form_dialog_gadget = hash.form_dialog_gadget;

        if (json_url === BROKEN_JSON_URL) {
          // Without the json description, it is not possible
          // to know the list of software types
          domsugar(page_container, {
            text: 'Sorry, it is not possible to fetch the Software Release informations.'
          });
          renderGadgetHeader(gadget, false, translation_dict);
          return;
        }

        parameter_xml = '<?xml version="1.0" encoding="UTF-8"?>' +
          (new XMLSerializer()).serializeToString(xml_document);

        return form_dialog_gadget.render({
          erp5_document: {
            "_embedded": {"_view": {
              // _actions is needed for form_dialog compatibility
              "_actions": {
                "put": "."
              },
              "your_title": {
                "title": "Title",
                "default": "",
                "required": 1,
                "editable": 1,
                "key": "title",
                "hidden": 0,
                "type": "StringField"
              },
              "your_instance_xml": {
                "title": "Instance Parameter",
                "url": "gadget_erp5_page_slap_parameter_form.html",
                "default": "",
                "renderjs_extra": JSON.stringify({
                  json_url: json_url,
                  parameter_xml: parameter_xml,
                  restricted_softwaretype: false
                }),
                "required": 1,
                "editable": 1,
                "key": "instance_xml",
                "hidden": 0,
                "type": "GadgetField"
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
            title: "Request",
            action: true,
            group_list: [
              ["left", [["your_title"]]],
              ["center", [["your_instance_xml"]]]
            ]
          }
        })
          .push(function () {
            domsugar(page_container, [form_dialog_gadget.element]);
            renderGadgetHeader(gadget, false, translation_dict, {});
          });
      });
  }

  function submitRequestDialog(gadget, translation_dict, data) {
    var xml_document = rJS.parseDocumentStringOrFail(
      data.text_content,
      "application/xml"
    ),
      i,
      parameter_list,
      len,
      json_document = {};

    // Convert the parameter_xml to json
    parameter_list = xml_document.getElementsByTagName("parameter");
    len = parameter_list.length;
    for (i = 0; i < len; i += 1) {
      json_document[parameter_list[i].getAttribute("id")] = parameter_list[i].textContent;
    }

    return callJsonRpcEntryPoint('/slapos.post.v0.software_instance', {
      title: data.title,
      software_release_uri: gadget.state.software_release_uri,
      software_type: data.software_type,
      shared: Boolean(data.shared),
      parameters: json_document
    })
      .push(function (response) {
        return gadget.redirectChangeState({
          display_step: DISPLAY_INSTANCE_TREE,
          instance_guid: response.instance_guid
        });
      }, function (error) {
        if (error.target instanceof XMLHttpRequest) {
          domsugar(page_container, {
            text: 'Sorry: ' + error.target.response.title
          });
          renderGadgetHeader(gadget, false, translation_dict);
          return;
        }
        throw error;
      });
  }

  //////////////////////////////////////////////////////
  // rJS Gadget
  //////////////////////////////////////////////////////
  rJS(window)
    .allowPublicAcquisition('notifyChange', function () {
      // Does nothing
      return;
    })
    .allowPublicAcquisition('getUrlParameter', function () {
      // Does nothing
      return;
    })
    .allowPublicAcquisition('updateHeader', function () {
      // Does nothing
      return;
    })
    .allowPublicAcquisition('getUrlFor', function () {
      // Does nothing
      return ".";
    })
    .allowPublicAcquisition('getUrlForList', function (param_list) {
      // Does nothing
      var arg_list = param_list[0],
        i,
        result_list = [];
      for (i = 0; i < arg_list.length; i += 1) {
        result_list.push(".");
      }
      return result_list;
    })
    .allowPublicAcquisition("getTranslationList", function getTranslationList(param_list) {
      return param_list[0];
    })
    .allowPublicAcquisition("translate", function translate(param_list) {
      return param_list[0];
    })

    .declareService(function () {
      // A service is triggered when this gadget is added to the DOM
      page_container = this.element.querySelector('div#slapproxy_page');
      return this.redirectChangeState({
        display_step: DISPLAY_INSTANCE_TREE_LIST
      });
    })

    .declareJob('redirectChangeState', function (new_state) {
      // It is required to defer the state change
      // to prevent "surprising" cancellation in case of exception
      // when submitting a form
      return this.changeState(new_state);
    })

    .onStateChange(function () {
      var gadget = this;
      return getTranslationDict(gadget)
        .push(function (translation_dict) {
          renderGadgetHeader(gadget, true, translation_dict);

          var render_method_dict = {};
          render_method_dict[DISPLAY_INSTANCE_TREE_LIST] = renderInstanceTreeList;
          render_method_dict[DISPLAY_INSTANCE_TREE] = renderInstanceTree;
          render_method_dict[DISPLAY_INSTANCE_TREE_UPDATE_DIALOG] = renderInstanceTreeUpdateDialog;
          render_method_dict[DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG] = renderSelectSoftwareReleaseRequestDialog;
          render_method_dict[DISPLAY_REQUEST_DIALOG] = renderRequestDialog;

          if (render_method_dict.hasOwnProperty(gadget.state.display_step)) {
            return render_method_dict[gadget.state.display_step](gadget, translation_dict);
          }
          throw new Error('Unhandled display step: ' + gadget.state.display_step);
        });
    })

    .onEvent("click", function (evt) {
      // Only handle click on BUTTON element
      var gadget = this,
        tag_name = evt.target.tagName;

      if ((tag_name !== 'BUTTON') ||
          (evt.target.type !== 'button') ||
          (!evt.target.dataset.display_step)) {
        return;
      }

      // Disable any button. It must be managed by this gadget
      evt.preventDefault();

      if (evt.target.dataset.display_step) {
        return gadget.redirectChangeState(evt.target.dataset);
      }

      throw new Error('Unhandled button: ' + evt.target.textContent);
    }, false, false)

    .allowPublicAcquisition("submitContent", function submitContent(param_list) {
      var gadget = this;
      return getTranslationDict(gadget)
        .push(function (translation_dict) {
          renderGadgetHeader(gadget, true, translation_dict);

          var submit_method_dict = {};
          submit_method_dict[DISPLAY_INSTANCE_TREE_UPDATE_DIALOG] = submitInstanceTreeUpdateDialog;
          submit_method_dict[DISPLAY_SELECT_SOFTWARE_RELEASE_REQUEST_DIALOG] = submitSelectSoftwareReleaseRequestDialog;
          submit_method_dict[DISPLAY_REQUEST_DIALOG] = submitRequestDialog;

          if (submit_method_dict.hasOwnProperty(gadget.state.display_step)) {
            return submit_method_dict[gadget.state.display_step](gadget, translation_dict, param_list[2]);
          }
          throw new Error('Unhandled submit step: ' + gadget.state.display_step);
        });
    })

    .allowPublicAcquisition("jio_allDocs", function jio_allDocs(param_list) {
      var search_method_dict = {},
        allDocs_args = param_list[0];

      search_method_dict[SEARCH_CONNECTION_PARAMETER] = searchConnectionParameterList;

      if (!search_method_dict.hasOwnProperty(allDocs_args.query)) {
        throw new Error('Unhandled search step: ' + allDocs_args.query);
      }

      return new RSVP.Queue(search_method_dict[allDocs_args.query](this, allDocs_args))
        .push(function (result_list) {
          var row_list = [],
            i;
          for (i = 0; i < result_list.length; i += 1) {
            row_list.push({
              value: result_list[i]
            });
          }
          return {
            data: {
              total_rows: result_list.length,
              rows: row_list
            }
          };
        });
    });

}(window, document, RSVP, rJS, XMLHttpRequest, URL,
  jIO, domsugar, XMLSerializer));