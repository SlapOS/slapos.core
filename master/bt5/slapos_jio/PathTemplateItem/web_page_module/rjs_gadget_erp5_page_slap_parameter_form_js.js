/*jslint nomen: true, maxlen: 200, indent: 2, unparam: true*/
/*global rJS, console, window, document, RSVP, btoa, atob, XMLSerializer,
         DOMParser, URI, vkbeautify, domsugar, Boolean */

(function (window, document, rJS, XMLSerializer, DOMParser, vkbeautify,
      domsugar, Boolean, URI) {
  "use strict";

  var DISPLAY_JSON_FORM = 'display_json_form',
    DISPLAY_RAW_XML = 'display_raw_xml';

  //////////////////////////////////////////
  // ParserError
  //////////////////////////////////////////
  function DOMParserError(message) {
    this.name = "DOMParserError";
    if ((message !== undefined) && (typeof message !== "string")) {
      throw new TypeError('You must pass a string for DOMParserError.');
    }
    this.message = message || "Default Message";
  }
  DOMParserError.prototype = new Error();
  DOMParserError.prototype.constructor = DOMParserError;

  //////////////////////////////////////////
  // DOMParser
  //////////////////////////////////////////
  function parseDocumentStringOrFail(string, mime_type) {
    var doc = new DOMParser().parseFromString(string, mime_type),
      error_node = doc.querySelector('parsererror');
    if (error_node !== null) {
      // parsing failed
      throw new DOMParserError(error_node.textContent);
    }
    return doc;
  }

  function jsonDictToParameterXML(json) {
    var parameter_id,
      xml_output = parseDocumentStringOrFail(
        '<?xml version="1.0" encoding="UTF-8" ?><instance />',
        'text/xml'
      ),
      xml_instance = xml_output.querySelector('instance'),
      xml_parameter;
    // Used by serialisation XML
    for (parameter_id in json) {
      if (json.hasOwnProperty(parameter_id)) {
        xml_parameter = xml_output.createElement('parameter');
        xml_parameter.textContent = json[parameter_id];
        xml_parameter.id = parameter_id;
        xml_instance.appendChild(xml_parameter);
      }
    }
    return vkbeautify.xml(
      (new XMLSerializer()).serializeToString(xml_output)
    );
  }

  function jsonDictToParameterJSONInXML(json) {
    var content = vkbeautify.json(JSON.stringify(json)),
      xml_output = parseDocumentStringOrFail(
        '<?xml version="1.0" encoding="UTF-8" ?>' +
          '<instance><parameter id="_">{}</parameter></instance>',
        'text/xml'
      );

    xml_output.querySelector('parameter[id="_"]').textContent = content;

    return vkbeautify.xml(
      (new XMLSerializer()).serializeToString(xml_output)
    );
  }

  function getFormValuesAsJSONDict(element) {
    var json_dict = {},
      entry,
      entry_list,
      multi_level_dict = {};
    element.querySelectorAll(".slapos-parameter").forEach(function (input, index) {
      var index_e, data_format = input.getAttribute("data-format");
      if (input.value !== "") {
        if (input.type === 'number') {
          json_dict[input.name] = parseFloat(input.value);
        } else if (input.tagName === "TEXTAREA") {
          if (data_format === "string") {
            json_dict[input.name] = input.value;
          } else if (data_format === "array") {
            json_dict[input.name] = input.value.split('\n');
          } else if (data_format === "array-number") {
            json_dict[input.name] = [];
            entry_list = input.value.split("\n");
            for (index_e in entry_list) {
              if (entry_list.hasOwnProperty(index_e)) {
                if (isNaN(parseFloat(entry_list[index_e]))) {
                  json_dict[input.name].push(entry_list[index_e]);
                } else {
                  json_dict[input.name].push(parseFloat(entry_list[index_e]));
                }
              }
            }
          } else {
            json_dict[input.name] = input.value.split('\n');
          }
        } else if (input.tagName === "SELECT") {
          if (data_format === "number" || data_format === "integer") {
            // Integer must use parseFloat, otherwise the value is rounded
            // loosing user's input.
            if (isNaN(parseFloat(input.value))) {
              json_dict[input.name] = input.value;
            } else {
              json_dict[input.name] = parseFloat(input.value);
            }
          } else if (input.getAttribute("data-format") === "boolean") {
            if (input.value === "true") {
              json_dict[input.name] = Boolean(input.value);
            } else if (input.value === "false") {
              json_dict[input.name] = false;
            } else {
              json_dict[input.name] = input.value;
            }
          } else {
            json_dict[input.name] = input.value;
          }
        } else {
          json_dict[input.name] = input.value;
        }
      }
    });

    function convertOnMultiLevel(key, value, d) {
      var i,
        kk,
        key_list = key.split("/");
      for (i = 2; i < key_list.length; i += 1) {
        kk = key_list[i];
        if (i === key_list.length - 1) {
          d[kk] = value;
        } else {
          if (!d.hasOwnProperty(kk)) {
            d[kk] = {};
          }
          d = d[kk];
        }
      }
    }

    for (entry in json_dict) {
      if (json_dict.hasOwnProperty(entry)) {
        convertOnMultiLevel(entry, json_dict[entry], multi_level_dict);
      }
    }
    return multi_level_dict;
  }

  function collapseParameter(element) {
    element.parentNode.querySelectorAll("div.subfield").forEach(function (div, i) {
      div.classList.toggle("display-none");
    });
    element.classList.toggle("slapos-parameter-dict-key-colapse");
    return element;
  }

  function removeSubParameter(element) {
    element.parentNode.parentNode.remove();
    return false;
  }

  function getSoftwareTypeFromForm(element) {
    var input = element.querySelector(".slapos-software-type");

    if (input !== undefined && input !== null) {
      return input.value;
    }
    return "";
  }

  function getSerialisationTypeFromForm(element) {
    var input = element.querySelector(".slapos-serialisation-type");

    if (input !== undefined && input !== null) {
      return input.value;
    }
    return "";
  }

  function getSchemaUrlFromForm(element) {
    var input = element.querySelector(".parameter_schema_url");

    if (input !== undefined && input !== null) {
      return input.value;
    }
    return "";
  }

  function showParameterForm(g) {
    var e = g.element.getElementsByTagName('select')[0],
      to_hide = g.element.querySelector("button.slapos-show-form"),
      to_show = g.element.querySelector("button.slapos-show-raw-parameter");

    if (e === undefined) {
      throw new Error("Select not found.");
    }

    to_hide.classList.add("display-none");
    to_show.classList.remove("display-none");

    return g.changeState({
      display_step: DISPLAY_JSON_FORM,
      softwareindex: e.selectedOptions[0]["data-id"],
      // Force refresh in any case
      render_timestamp: new Date().getTime()
    });
  }

  function showRawParameter(g) {
    var e = g.element.querySelector("button.slapos-show-raw-parameter"),
      to_show = g.element.querySelector("button.slapos-show-form");

    e.classList.add("display-none");
    to_show.classList.remove("display-none");

    return g.changeState({
      display_step: DISPLAY_RAW_XML,
      // Force refresh in any case
      render_timestamp: new Date().getTime()
    });
  }

  function updateParameterForm(g) {
    var e = g.element.getElementsByTagName('select')[0],
      parameter_shared = g.element.querySelector('input.parameter_shared');

    if (e === undefined) {
      throw new Error("Select not found.");
    }

    parameter_shared.value = e.selectedOptions[0]["data-shared"];
    return g.changeState({
      softwareindex: e.selectedOptions[0]["data-id"],
      // Force refresh in any case
      render_timestamp: new Date().getTime()
    });
  }

  /////////////////////////////////////////////////////
  // check the form validity
  /////////////////////////////////////////////////////
  function checkValidity(g) {
    var json_url = g.state.json_url,
      software_type = getSoftwareTypeFromForm(g.element),
      json_dict = getFormValuesAsJSONDict(g.element),
      schema_url = getSchemaUrlFromForm(g.element),
      serialisation_type = getSerialisationTypeFromForm(g.element);

    if (software_type === "") {
      if (g.state.shared) {
        throw new Error("The software type is not part of the json (" + software_type + " as slave)");
      }
      throw new Error("The software type is not part of the json (" + software_type + ")");
    }

    return g.getBaseUrl(json_url)
      .push(function (base_url) {
        return g.validateJSON(base_url, schema_url, json_dict);
      })
      .push(function (validation) {
        var error_index,
          parameter_hash_input = g.element.querySelectorAll('.parameter_hash_output')[0],
          field_name,
          div,
          xml_output,
          input_field,
          error_dict;

        g.element.querySelectorAll("span.error").forEach(function (span, i) {
          span.textContent = "";
        });

        g.element.querySelectorAll("div.error-input").forEach(function (div, i) {
          div.setAttribute("class", "");
        });

        if (serialisation_type === "json-in-xml") {
          xml_output = jsonDictToParameterJSONInXML(json_dict);
        } else {
          xml_output = jsonDictToParameterXML(json_dict);
        }
        parameter_hash_input.value = btoa(xml_output);

        // Update fields if errors exist
        for (error_index in validation.errors) {
          if (validation.errors.hasOwnProperty(error_index)) {
            error_dict = validation.errors[error_index];
            // error_dict = { error : "", instanceLocation: "#", keyword: "", keywordLocation: "" }
            field_name = error_dict.instanceLocation.slice(1);
            if (field_name !== "") {
              input_field = g.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
              if (input_field === null) {
                field_name = field_name.split("/").slice(0, -1).join("/");
                input_field = g.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
              }
              if (input_field !== null) {
                div = input_field.parentNode;
                div.setAttribute("class", "slapos-parameter error-input");
                div.querySelector("span.error").textContent = validation.errors[error_index].error;
              }
            } else if (error_dict.keyword === "required") {
              // Specific use case for required
              field_name = "/" + error_dict.key;
              input_field = g.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
              if (input_field === null) {
                field_name = field_name.split("/").slice(0, -1).join("/");
                input_field = g.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
              }
              if (input_field !== null) {
                div = input_field.parentNode;
                div.setAttribute("class", "slapos-parameter error-input");
                div.querySelector("span.error").textContent = error_dict.error;
              }
            }
          }
        }
        return xml_output;
      });
  }

  /////////////////////////////////////////////////////
  // main render display functions
  /////////////////////////////////////////////////////
  function renderDisplayRawXml(g, error_text) {
    var fieldset = g.element.querySelector('fieldset.parameter-optional'),
      failover_div = g.element.querySelector('div.failover-textarea'),
      div_error,
      textarea,
      show_raw_button = g.element.querySelector("button.slapos-show-raw-parameter"),
      show_form_button = g.element.querySelector("button.slapos-show-form");

    if (error_text) {
      if (show_raw_button !== null) {
        show_raw_button.classList.add("display-none");
      }

      if (show_form_button !== null) {
        show_form_button.classList.remove("display-none");
      }

      div_error = domsugar('div', {
        'class': 'error'
      }, [
        domsugar('span', {
          'class': 'error',
          text: "Parameter form is not available, use the textarea above for edit the instance parameters."
        }),
        domsugar('details', [
          domsugar('summary', {
            text: "More information..."
          }),
          domsugar('span', {
            'class': 'error_msg',
            text: error_text
          })
        ])
      ]);
    } else {
      div_error = domsugar('div');
    }
    textarea = domsugar('textarea', {
      rows: "10",
      cols: "80",
      name: "text_content",
      text: g.state.parameter_xml
    });
    if (!g.state.editable) {
      textarea.setAttribute("readonly", true);
    }

    return g.renderSubForm({}, {}, true)
      .push(function () {
        // Do not hide the Software type, let the user edit it.
        failover_div = domsugar(failover_div, {}, [
          domsugar('div', {
            'class': 'field'
          }, [
            textarea
          ]),
          // div error
          div_error
        ]);
        fieldset = domsugar(fieldset);
        return failover_div;
      });
  }

  function renderDisplayJsonForm(gadget) {

    var serialisation = gadget.state.serialisation,
      json_url = gadget.state.json_url,
      parameter_xml = gadget.state.parameter_xml,
      shared = gadget.state.shared,
      softwaretype = gadget.state.softwaretype,
      softwareindex = gadget.state.softwareindex,
      editable = gadget.state.editable,
      to_hide = gadget.element.querySelector("button.slapos-show-form"),
      to_show = gadget.element.querySelector("button.slapos-show-raw-parameter");

    if (json_url === undefined) {
      throw new Error("undefined json_url");
    }

    if (to_hide !== null) {
      to_hide.classList.add("display-none");
    }

    if (to_show !== null) {
      to_show.classList.remove("display-none");
    }
    return gadget.loadSoftwareJSON(json_url)
      .push(function (json) {
        var option_index,
          option,
          option_selected = softwaretype,
          option_selected_index = softwareindex,
          input = gadget.element.querySelector('select.slapos-software-type'),
          parameter_shared = gadget.element.querySelector('input.parameter_shared'),
          parameter_schema_url = gadget.element.querySelector('input.parameter_schema_url'),
          s_input = gadget.element.querySelector('input.slapos-serialisation-type'),
          selection_option_list = [],
          lowest_index = 999,
          lowest_option_index;

        if (!editable || gadget.state.restricted_softwaretype === true) {
          input.classList.add("readonly");
          input["aria-disabled"] = "true";
          input["tab-index"] = "-1";
        }

        if (input.children.length === 0) {
          if (option_selected === undefined) {
            // search by the lowest index
            for (option_index in json['software-type']) {
              if (json['software-type'].hasOwnProperty(option_index)) {
                if ((gadget.state.software_type_list.length === 0) ||
                    (gadget.state.software_type_list.includes(option_index))) {
                  if (json['software-type'][option_index].index === undefined) {
                    json['software-type'][option_index].index = 999;
                  }

                  if (json['software-type'][option_index].index < lowest_index) {
                    lowest_index = json['software-type'][option_index].index;
                    lowest_option_index = option_index;
                  }
                }
              }
            }
          }

          for (option_index in json['software-type']) {
            if (json['software-type'].hasOwnProperty(option_index)) {
              if ((gadget.state.software_type_list.length === 0) ||
                  (gadget.state.software_type_list.includes(option_index)) ||
                  (gadget.state.software_type_list.includes(json['software-type'][option_index]['software-type']))) {

                if (json['software-type'][option_index].shared === undefined) {
                  json['software-type'][option_index].shared = false;
                }

                option = domsugar("option", {
                  text: json['software-type'][option_index].title,
                  value: option_index
                });
                option['data-id'] = option_index;
                option['data-index'] = 999;
                option['data-shared'] = json['software-type'][option_index].shared;

                if (json['software-type'][option_index]['software-type'] !== undefined) {
                  option.value = json['software-type'][option_index]['software-type'];
                }

                if (json['software-type'][option_index].index) {
                  option['data-index'] = json['software-type'][option_index].index;
                }

                if (option_index === lowest_option_index) {
                  option_selected = option.value;
                  option.selected = true;
                  option_selected_index = option_index;
                  if (json['software-type'][option_index].shared === true) {
                    parameter_shared.value = true;
                  } else {
                    parameter_shared.value = false;
                  }
                  if (shared === undefined) {
                    shared = parameter_shared.value;
                  }
                }

                if ((option_selected_index === undefined) &&
                    (option.value === option_selected) &&
                    (Boolean(shared) === Boolean(json['software-type'][option_index].shared))) {
                  option.selected = true;
                  option_selected_index = option_index;
                  if (json['software-type'][option_index].shared === true) {
                    parameter_shared.value = true;
                  } else {
                    parameter_shared.value = false;
                  }
                }

                if (gadget.state.restricted_softwaretype === true) {
                  if (option.value === softwaretype) {
                    if (Boolean(shared) === Boolean(json['software-type'][option_index].shared)) {
                      selection_option_list.push(option);
                      // We expect a single possible occurence per software type
                      break;
                    }
                  }
                } else {
                  selection_option_list.push(option);
                }
              }
            }
          }
        }

        selection_option_list.sort(function (a, b) {
          return a["data-index"] - b["data-index"];
        });

        for (option_index in selection_option_list) {
          if (selection_option_list.hasOwnProperty(option_index)) {
            input.appendChild(selection_option_list[option_index]);
          }
        }

        if (softwaretype === undefined) {
          softwaretype = option_selected;
        }
        if (input.children.length === 0) {
          if (shared) {
            throw new Error("The software type is not part of the json (" + softwaretype + " as slave)");
          }
          throw new Error("The software type is not part of the json (" + softwaretype + ")");
        }
        if (json['software-type'][option_selected_index] === undefined) {
          throw new Error("The sotware type is not part of the json (" + softwaretype + ")");
        }

        if (json['software-type'][option_selected_index].serialisation !== undefined) {
          s_input.value = json['software-type'][option_selected_index].serialisation;
          serialisation = json['software-type'][option_selected_index].serialisation;
        } else {
          s_input.value = json.serialisation;
          serialisation = json.serialisation;
        }

        // Save current schema on the field
        parameter_schema_url.value = json['software-type'][option_selected_index].request;

        return parameter_schema_url.value;
      })
      .push(function (parameter_json_schema_url) {
        var parameter_dict = {}, parameter_list, json_url_uri, prefix, parameter_entry;

        if (parameter_xml !== undefined) {
          if (serialisation === "json-in-xml") {
            parameter_list = parseDocumentStringOrFail(
              parameter_xml,
              'text/xml'
            ).querySelectorAll("parameter");

            if (parameter_list.length > 1) {
              throw new Error("The current parameter should contains only _ parameter (json-in-xml).");
            }
            parameter_entry = parseDocumentStringOrFail(
              parameter_xml,
              'text/xml'
            ).querySelector("parameter[id='_']");

            if (parameter_entry !== null) {
              parameter_dict = JSON.parse(parameter_entry.textContent);
            } else if (parameter_list.length === 1) {
              throw new Error(
                "The current parameter should contains only _ parameter (json-in-xml)."
              );
            }
          } else if (["", "xml"].indexOf(serialisation) >= 0) {
            parameter_entry = parseDocumentStringOrFail(
              parameter_xml,
              'text/xml'
            ).querySelector("parameter[id='_']");

            if (parameter_entry !== null) {
              throw new Error("The current parameter values should NOT contains _ parameter (xml).");
            }
            parseDocumentStringOrFail(
              parameter_xml,
              'text/xml'
            ).querySelectorAll("parameter")
                .forEach(function (element, index) {
                parameter_dict[element.id] = element.textContent;
              });
          } else {
            throw new Error("Unknown serialisation: " + serialisation);
          }
        }

        if (URI(parameter_json_schema_url).protocol() === "") {
          // URL is relative, turn into absolute
          json_url_uri = URI(json_url);
          prefix = json_url_uri.path().split("/");
          prefix.pop();
          prefix = json_url.split(json_url_uri.path())[0] + prefix.join("/");
          parameter_json_schema_url = prefix + "/" + parameter_json_schema_url;
        }
        return gadget.loadJSONSchema(parameter_json_schema_url, serialisation)
          .push(function (json) {
            // Reset failover text area
            domsugar(gadget.element.querySelector('div.failover-textarea'));
            return gadget.renderSubForm(
              json,
              parameter_dict,
              editable
            );
          });
      })
      .push(function () {
        var i, div_list = gadget.element.querySelectorAll('.slapos-parameter-dict-key > div'),
          label_list = gadget.element.querySelectorAll('label.slapos-parameter-dict-key');

        for (i = 0; i < div_list.length; i = i + 1) {
          // This should be replaced by a proper class hidden-div
          div_list[i].classList.add('display-none');
        }

        for (i = 0; i < label_list.length; i = i + 1) {
          label_list[i].classList.add("slapos-parameter-dict-key-colapse");
        }
      })

      .fail(function (error) {
        console.warn(error);
        console.log(error.stack);
        return renderDisplayRawXml(gadget, error.toString());
      });
  }

  /////////////////////////////////////////////////////
  // Gadget methods
  /////////////////////////////////////////////////////
  rJS(window)
    .setState({
      display_step: DISPLAY_JSON_FORM
    })
    .declareMethod("loadJSONSchema", function (url, serialisation) {
      return this.getDeclaredGadget('loadschema')
        .push(function (gadget) {
          return gadget.loadJSONSchema(url, serialisation);
        });
    })

    .declareMethod("validateJSON", function (base_url, schema_url, generated_json) {
      return this.getDeclaredGadget('loadschema')
        .push(function (gadget) {
          return gadget.validateJSON(base_url, schema_url, generated_json);
        });
    })

    .declareMethod("getBaseUrl", function (url) {
      return this.getDeclaredGadget('loadschema')
        .push(function (gadget) {
          return gadget.getBaseUrl(url);
        });
    })
    .declareMethod("loadSoftwareJSON", function (url) {
      return this.getDeclaredGadget('loadschema')
        .push(function (gadget) {
          return gadget.loadSoftwareJSON(url);
        });
    })

    .declareMethod("renderSubForm", function (json_field, default_dict, editable) {
      return this.getDeclaredGadget('json_form')
        .push(function (gadget) {
          return gadget.render({
            json_field: json_field,
            default_dict: default_dict,
            editable: editable
          });
        });
    })

    .declareMethod('render', function (options) {
      var restricted_softwaretype = false,
        software_type_list = [],
        parameter_hash = options.value.parameter.parameter_hash,
        // XXX Do we directly get parameter_xml parameter?
        parameter_xml = options.value.parameter.parameter_xml;

      if (parameter_hash !== undefined) {
        // A JSON where provided via gadgetfield
        parameter_xml = atob(parameter_hash);
      }

      if (options.value.parameter.software_type_list !== undefined) {
        software_type_list = options.value.parameter.software_type_list;
      }

      if (options.value.parameter.softwaretype !== undefined) {
        restricted_softwaretype = true;
        // exceptional situation where the default item must be in
        // the list. 
        software_type_list.push(options.value.parameter.softwaretype);
      }

      return this.changeState({
        // Not used parameters
        // hidden: options.hidden,
        // key: options.key,
        serialisation: options.serialisation,
        json_url: options.value.parameter.json_url,
        parameter_xml: parameter_xml,
        restricted_softwaretype: restricted_softwaretype,
        shared: options.value.parameter.shared,
        softwaretype: options.value.parameter.softwaretype,
        software_type_list: software_type_list,
        softwareindex: options.value.parameter.softwareindex,
        editable: options.editable,
        // Force refresh in any case
        render_timestamp: new Date().getTime()
      });
    })
    .onStateChange(function () {
      if (this.state.display_step === DISPLAY_JSON_FORM) {
        return renderDisplayJsonForm(this);
      }
      if (this.state.display_step === DISPLAY_RAW_XML) {
        return renderDisplayRawXml(this);
      }
      throw new Error('Unhandled display step: ' + this.state.display_step);
    })

    .onEvent("change", function (evt) {
      var gadget = this,
        software_type_element = gadget.element.getElementsByTagName('select')[0];

      if (evt.target === software_type_element) {
        return updateParameterForm(gadget);
      }

      // @ts-ignore
      if (evt.target.className.indexOf("slapos-parameter") !== -1) {
        // getContent is protected by a mutex which prevent
        // onchangestate to be called in parallel
        return gadget.getContent();
      }

    }, false, false)

    .onEvent("click", function (evt) {
      // Only handle click on BUTTON element
      var gadget = this,
        queue,
        // @ts-ignore
        tag_name = evt.target.tagName;

      if ((tag_name === 'LABEL') &&
          // @ts-ignore
          (evt.target.className.indexOf("slapos-parameter-dict-key") !== -1)) {
        return collapseParameter(evt.target);
      }

      if ((tag_name === 'SPAN') &&
          // @ts-ignore
          (evt.target.className.indexOf("bt_close") !== -1)) {
        return removeSubParameter(evt.target);
      }

      if (tag_name === 'BUTTON') {
        // Disable any button. It must be managed by this gadget
        evt.preventDefault();
      }

      // Always get content to ensure the possible displayed form
      // is checked and content propagated to the gadget state value
      queue = gadget.getContent();

      if ((tag_name === 'BUTTON') &&
          // @ts-ignore
          (evt.target.className.indexOf("slapos-show-form") !== -1)) {
        return queue
          .push(function () {
            return showParameterForm(gadget);
          });
      }

      if ((tag_name === 'BUTTON') &&
          // @ts-ignore
          (evt.target.className.indexOf("slapos-show-raw-parameter") !== -1)) {
        return queue
          .push(function () {
            return showRawParameter(gadget);
          });
      }
    }, false, false)

    .declareMethod('getContent', function () {
      var gadget = this,
        content_dict = {};
      return gadget.getElement()
        .push(function (element) {
          var text_content = element.querySelector('textarea[name=text_content]'),
            software_type = element.querySelector('select[name=software_type]'),
            shared = element.querySelector('input[name=shared]');
          if (software_type !== null) {
            gadget.state.softwaretype = software_type.value;
            content_dict.software_type = software_type.value;
          }
          if ((shared  !== null) && (shared.value === "true")) {
            gadget.state.shared = 1;
            content_dict.shared = 1;
          }
          if (!gadget.state.editable) {
            return gadget.state.parameter_xml;
          }
          if (text_content !== null) {
            // Don't provide blank string since the parameter will not able to load
            // itself. If the user removed the values, provide an empty parameter default.
            if (text_content.value === "") {
              return '<?xml version="1.0" encoding="utf-8" ?><instance></instance>';
            }
            return text_content.value;
          }
          return checkValidity(gadget);
        })
        .push(function (xml_result) {
          // Update gadget state
          gadget.state.parameter_xml = xml_result;
          content_dict.text_content = xml_result;
          return content_dict;
        });
    }, {mutex: 'statechange'});

}(window, document, rJS, XMLSerializer, DOMParser, vkbeautify,
    domsugar, Boolean, URI));
