/*jslint nomen: true, maxlen: 200, indent: 2, unparam: true*/
/*global rJS, console, window, document, RSVP, btoa, atob, $, XMLSerializer,
         jQuery, URI, vkbeautify, domsugar, Boolean */

(function (window, document, rJS, $, XMLSerializer, jQuery, vkbeautify,
           loopEventListener, domsugar, Boolean) {
  "use strict";

  var DISPLAY_JSON_FORM = 'display_json_form',
    DISPLAY_RAW_XML = 'display_raw_xml';

  function jsonDictToParameterXML(json) {
    var parameter_id,
      xml_output = $($.parseXML('<?xml version="1.0" encoding="UTF-8" ?>\n<instance />'));
    // Used by serialisation XML
    for (parameter_id in json) {
      if (json.hasOwnProperty(parameter_id)) {
        $('instance', xml_output).append(
          $('<parameter />', xml_output)
            .text(json[parameter_id])
              .attr({id: parameter_id})
        );
      }
    }
    return vkbeautify.xml(
      (new XMLSerializer()).serializeToString(xml_output.context)
    );
  }

  function jsonDictToParameterJSONInXML(json) {
    var xml_output = $($.parseXML('<?xml version="1.0" encoding="UTF-8" ?>\n<instance />'));
      // Used by serialisation XML
    $('instance', xml_output).append(
      $('<parameter />', xml_output)
          .text(vkbeautify.json(JSON.stringify(json)))
            .attr({id: "_"})
    );
    return vkbeautify.xml(
      (new XMLSerializer()).serializeToString(xml_output.context)
    );
  }

  function render_selection(json_field, default_value) {
    var option_list = [domsugar('option', {
      value: "",
      selected: (default_value === undefined)
    })],
      option_index,
      data_format = "string";

    if (json_field.type === "integer" || json_field.type === "number") {
      data_format = "number";
    }
    
    for (option_index in json_field['enum']) {
      if (json_field['enum'].hasOwnProperty(option_index)) {
        option_list.push(domsugar('option', {
          value: json_field['enum'][option_index],
          text: json_field['enum'][option_index],
          "data-format": data_format,
          selected: (
            json_field['enum'][option_index].toString() === default_value
          )
        }));
      }
    }
    return domsugar('select', {
      size: 1,
      "data-format": data_format
    }, option_list);
  }

  function render_selection_oneof(json_field, default_value) {
    var option_list = [domsugar('option', {
      value: "",
      selected: (default_value === undefined)
    })];

    json_field.oneOf.forEach(function (element) {
      if ((element['const'] !== undefined) && (element.title !== undefined)) {
        var value;
        if ((json_field.type === 'array') || (json_field.type === 'object')) {
          // Support for unusual types
          value = JSON.stringify(element['const']);
        } else {
          value = element['const'];
        }
        option_list.push(domsugar('option', {
          value: value,
          text: element.title,
          selected: (value === default_value)
        }));
      }
    });

    return domsugar('select', {
      size: 1
    }, option_list);
  }

  function render_textarea(json_field, default_value, data_format) {
    var value = '';
    if (default_value !== undefined) {
      if (default_value instanceof Array) {
        value = default_value.join("\n");
      } else {
        value = default_value;
      }
    }
    return domsugar('textarea', {
      value: value,
      "data-format": data_format
    });
  }

  function render_field(json_field, default_value) {
    if (json_field['enum'] !== undefined) {
      return render_selection(json_field, default_value);
    }

    if (json_field.oneOf !== undefined) {
      return render_selection_oneof(json_field, default_value);
    }

    if (json_field.type === "boolean") {
      json_field['enum'] = [true, false];
      if (default_value === "true") {
        default_value = true;
      }
      if (default_value === "false") {
        default_value = false;
      }
      return render_selection(json_field, default_value);
    }

    if (json_field.type === "array") {
      return render_textarea(json_field, default_value, "array");
    }

    if (json_field.type === "string" && json_field.textarea === true) {
      return render_textarea(json_field, default_value, "string");
    }

    var domsugar_input_dict = {};

    if (default_value !== undefined) {
      domsugar_input_dict.value = default_value;
    }

    if (json_field.type === "integer") {
      domsugar_input_dict.type = "number";
    } else if (json_field.type === "number") {
      domsugar_input_dict.type = "number";
      domsugar_input_dict.step = "any";
    } else if (json_field.type === "hidden") {
      domsugar_input_dict.type = "hidden";
    } else {
      domsugar_input_dict.type = "text";
    }

    return domsugar('input', domsugar_input_dict);
  }

  function render_subform(json_field, default_dict, root, path, restricted) {
    var div_input,
      key,
      div,
      label,
      input,
      default_value,
      default_used_list = [],
      default_div,
      span_error,
      span_info;

    if (default_dict === undefined) {
      default_dict = {};
    }

    if (path === undefined) {
      path = "/";
    }

    if (json_field.patternProperties !== undefined) {
      if (json_field.patternProperties['.*'] !== undefined) {

        div = domsugar("div", {
          "class": "subfield",
          title: json_field.description
        });

        if (restricted !== true) {
          div_input = domsugar("div", {
            "class": "input"
          }, [
            domsugar('input', {
              type: "text",
              // Name is only meaningfull to automate tests
              name: "ADD" + path
            }),
            domsugar('button', {
              value: btoa(JSON.stringify(json_field.patternProperties['.*'])),
              "class": "add-sub-form",
              type: "button",
              name: path,
              text: "+"
            })
          ]);

          div.appendChild(div_input);
        }

        for (default_value in default_dict) {
          if (default_dict.hasOwnProperty(default_value)) {
            default_div = domsugar("div", {
              "class": "slapos-parameter-dict-key"
            }, [
              domsugar('label', {
                text: default_value,
                'class': "slapos-parameter-dict-key"
              }, [
                domsugar('span', {
                  text: "×",
                  "class": "bt_close CLOSE" + path + "/" + default_value,
                  title: "Remove this parameter section."
                })
              ])
            ]);

            div.appendChild(render_subform(
              json_field.patternProperties['.*'],
              default_dict[default_value],
              default_div,
              path + "/" + default_value,
              restricted
            ));
          }
        }
        root.appendChild(div);

        return div;
      }
    }

    for (key in json_field.properties) {
      if (json_field.properties.hasOwnProperty(key)) {
        div = document.createElement("div");
        div.setAttribute("class", "subfield");
        div.title = json_field.properties[key].description;
        /* console.log(key); */
        label = document.createElement("label");
        label.textContent = json_field.properties[key].title;
        div.appendChild(label);
        div_input = document.createElement("div");
        div_input.setAttribute("class", "input");
        if (json_field.properties[key].type === 'object') {
          label.setAttribute("class", "slapos-parameter-dict-key");
          div_input = render_subform(json_field.properties[key],
            default_dict[key],
            div_input,
            path + "/" + key,
            restricted);
        } else {
          input = render_field(json_field.properties[key], default_dict[key]);
          input.name = path + "/" + key;
          input.setAttribute("class", "slapos-parameter");
          input.setAttribute("placeholder", " ");
          div_input.appendChild(input);
        }
        default_used_list.push(key);
        if (json_field.properties[key]['default'] !== undefined) {
          span_info = document.createElement("span");
          span_info.textContent = '(default = ' + json_field.properties[key]['default'] + ')';
          div_input.appendChild(span_info);
        }
        span_error = document.createElement("span");
        span_error.setAttribute("class", "error");
        div_input.appendChild(span_error);
        div.appendChild(div_input);
        root.appendChild(div);
      }
    }
    for (key in default_dict) {
      if (default_dict.hasOwnProperty(key)) {
        if (default_used_list.indexOf(key) < 0) {
          div = document.createElement("div");
          div.title = key;
          if (typeof default_dict[key] === 'object') {
            div_input = document.createElement("div");
            div_input.setAttribute("class", "input");
            label.setAttribute("class", "slapos-parameter-dict-key");
            div_input = render_subform({},
              default_dict[key],
              div_input,
              path + "/" + key,
              restricted);
          } else if (restricted === true) {
            div_input = document.createElement("div");
            div_input.setAttribute("class", "input");
            input = render_field({"type": "hidden"}, default_dict[key]);
            input.name = path + "/" + key;
            input.setAttribute("class", "slapos-parameter");
            input.setAttribute("placeholder", " ");
            div_input.appendChild(input);
          } else {
            div.setAttribute("class", "subfield");
            label = document.createElement("label");
            label.textContent = key;
            div.appendChild(label);
            div_input = document.createElement("div");
            div_input.setAttribute("class", "input");
            input = render_field({"type": "string", "textarea": true}, default_dict[key]);
            input.name = path + "/" + key;
            input.setAttribute("class", "slapos-parameter");
            input.setAttribute("placeholder", " ");
            div_input.appendChild(input);
            span_info = document.createElement("span");
            span_info.textContent = '(Not part of the schema)';
            div_input.appendChild(span_info);
            span_error = document.createElement("span");
            span_error.setAttribute("class", "error");
            div_input.appendChild(span_error);
          }
          default_used_list.push(key);
          div.appendChild(div_input);
          root.appendChild(div);

        }
      }
    }
    return root;
  }

  function getFormValuesAsJSONDict(element) {
    var json_dict = {},
      entry,
      multi_level_dict = {};
    $(element.querySelectorAll(".slapos-parameter")).each(function (key, input) {
      if (input.value !== "") {
        if (input.type === 'number') {
          json_dict[input.name] = parseFloat(input.value);
        } else if (input.value === "true") {
          json_dict[input.name] = true;
        } else if (input.value === "false") {
          json_dict[input.name] = false;
        } else if (input.tagName === "TEXTAREA") {
          if (input.getAttribute("data-format") === "string") {
            json_dict[input.name] = input.value;
          } else {
            json_dict[input.name] = input.value.split('\n');
          }
        } else if (input.tagName === "SELECT") {
          if (input.getAttribute("data-format") === "number") {
            json_dict[input.name] = parseFloat(input.value);
          } else if (input.getAttribute("data-format") === "integer") {
            // Don't use parseInt since it will round the value, modifing the
            // use input. So we keep it the value.
            json_dict[input.name] = parseFloat(input.value);
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
    $(element).parent().children("div").toggle(300);
    if ($(element).hasClass("slapos-parameter-dict-key-colapse")) {
      $(element).removeClass("slapos-parameter-dict-key-colapse");
    } else {
      $(element).addClass("slapos-parameter-dict-key-colapse");
    }
    console.log("COLLAPSED");
    return element;
  }

  function removeSubParameter(element) {
    $(element).parent().parent().remove();
    return false;
  }

  function addSubForm(gadget, element) {
    var subform_json = JSON.parse(atob(element.value)),
      input_text = element.parentNode.querySelector("input[type='text']"),
      div;

    if (input_text.value === "") {
      return false;
    }

    div = domsugar('div', {
      'class': "slapos-parameter-dict-key"
    }, [domsugar('label', {
      'class': "slapos-parameter-dict-key",
      text: input_text.value
    })]);

    div = render_subform(subform_json, {}, div, element.name + "/" + input_text.value);

    element.parentNode.parentNode.insertBefore(div, element.parentNode.parentNode.children[1]);
    // element.parentNode.parentNode.appendChild(div);

    return div;
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

    $(to_hide).addClass("hidden-button");
    $(to_show).removeClass("hidden-button");

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

    $(e).addClass("hidden-button");
    $(to_show).removeClass("hidden-button");

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
          divm,
          missing_index,
          missing_field_name,
          xml_output;

        $(g.element.querySelectorAll("span.error")).each(function (i, span) {
          span.textContent = "";
        });

        $(g.element.querySelectorAll("div.error-input")).each(function (i, div) {
          div.setAttribute("class", "");
        });
        if (serialisation_type === "json-in-xml") {
          xml_output = jsonDictToParameterJSONInXML(json_dict);
        } else {
          xml_output = jsonDictToParameterXML(json_dict);
        }
        parameter_hash_input.value = btoa(xml_output);
        // g.options.value.parameter.parameter_hash = btoa(xml_output);
        // console.log(parameter_hash_input.value);
        // console.log(xml_output);
        if (validation.valid) {
          return xml_output;
        }
        for (error_index in validation.errors) {
          if (validation.errors.hasOwnProperty(error_index)) {
            field_name = validation.errors[error_index].dataPath;
            div = $(".slapos-parameter[name='/" + field_name  + "']")[0].parentNode;
            div.setAttribute("class", "slapos-parameter error-input");
            div.querySelector("span.error").textContent = validation.errors[error_index].message;
          }
        }

        for (missing_index in validation.missing) {
          if (validation.missing.hasOwnProperty(missing_index)) {
            missing_field_name = validation.missing[missing_index].dataPath;
            divm = $('.slapos-parameter[name=/' + missing_field_name  + "']")[0].parentNode;
            divm.setAttribute("class", "error-input");
            divm.querySelector("span.error").textContent = validation.missing[missing_index].message;
          }
        }
        return "ERROR";
      });
  }

  /////////////////////////////////////////////////////
  // main render display functions
  /////////////////////////////////////////////////////
  function renderDisplayRawXml(g, error_text) {
    var fieldset,
      fieldset_list = g.element.querySelectorAll('fieldset'),
      div_error,
      show_raw_button = g.element.querySelector("button.slapos-show-raw-parameter"),
      show_form_button = g.element.querySelector("button.slapos-show-form");

    if (error_text) {
      if (show_raw_button !== null) {
        $(show_raw_button).addClass("hidden-button");
      }

      if (show_form_button !== null) {
        $(show_form_button).removeClass("hidden-button");
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
    fieldset = domsugar('fieldset', [
      domsugar('div', {
        'class': 'field'
      }, [
        domsugar('textarea', {
          rows: "10",
          cols: "80",
          name: "text_content",
          text: g.state.parameter_xml
        })
      ]),
      // div error
      div_error
    ]);

    // Do not hide the Software type, let the user edit it.
    $(fieldset_list[1]).replaceWith(fieldset);
    fieldset_list[2].innerHTML = '';

    return fieldset;
  }

  function renderDisplayJsonForm(gadget) {

    var serialisation = gadget.state.serialisation,
      json_url = gadget.state.json_url,
      parameter_xml = gadget.state.parameter_xml,
      restricted_softwaretype = gadget.state.restricted_softwaretype,
      restricted_parameter = gadget.state.restricted_parameter,
      shared = gadget.state.shared,
      softwaretype = gadget.state.softwaretype,
      softwareindex = gadget.state.softwareindex,
      to_hide = gadget.element.querySelector("button.slapos-show-form"),
      to_show = gadget.element.querySelector("button.slapos-show-raw-parameter");

    if (json_url === undefined) {
      throw new Error("undefined json_url");
    }

    if (to_hide !== null) {
      $(to_hide).addClass("hidden-button");
    }

    if (to_show !== null) {
      $(to_show).removeClass("hidden-button");
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

        if (input.children.length === 0) {
          if (option_selected === undefined) {
            // search by the lowest index
            for (option_index in json['software-type']) {
              if (json['software-type'].hasOwnProperty(option_index)) {
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

          for (option_index in json['software-type']) {
            if (json['software-type'].hasOwnProperty(option_index)) {
              option = document.createElement("option");
              if (json['software-type'][option_index]['software-type'] !== undefined) {
                option.value = json['software-type'][option_index]['software-type'];
              } else {
                option.value = option_index;
              }

              option['data-id'] = option_index;
              option.textContent = json['software-type'][option_index].title;
              if (json['software-type'][option_index].index) {
                option['data-index'] = json['software-type'][option_index].index;
              } else {
                option['data-index'] = 999;
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

              if (json['software-type'][option_index].shared === undefined) {
                json['software-type'][option_index].shared = false;
              }

              option['data-shared'] = json['software-type'][option_index].shared;

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

              if (restricted_softwaretype === true) {
                if (option.value === softwaretype) {
                  if (Boolean(shared) === Boolean(json['software-type'][option_index].shared)) {
                    selection_option_list.push(option);
                  }
                }
              } else {
                selection_option_list.push(option);
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
            parameter_list = jQuery.parseXML(
              parameter_xml
            ).querySelectorAll("parameter");
            if (parameter_list.length > 1) {
              throw new Error("The current parameter should contains only _ parameter (json-in-xml).");
            }
            parameter_entry = jQuery.parseXML(
              parameter_xml
            ).querySelector("parameter[id='_']");
            if (parameter_entry !== null) {
              parameter_dict = JSON.parse(parameter_entry.textContent);
            } else if (parameter_list.length === 1) {
              throw new Error(
                "The current parameter should contains only _ parameter (json-in-xml)."
              );
            }
          } else if (["", "xml"].indexOf(serialisation) >= 0) {
            parameter_entry = jQuery.parseXML(
              parameter_xml
            ).querySelector("parameter[id='_']");
            if (parameter_entry !== null) {
              throw new Error("The current parameter values should NOT contains _ parameter (xml).");
            }
            $(jQuery.parseXML(parameter_xml)
              .querySelectorAll("parameter"))
                .each(function (key, p) {
                parameter_dict[p.id] = p.textContent;
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
            var fieldset_list = gadget.element.querySelectorAll('fieldset'),
              fieldset = document.createElement("fieldset");

            fieldset = render_subform(json, parameter_dict, fieldset, undefined, restricted_parameter);
            $(fieldset_list[1]).replaceWith(fieldset);
            return fieldset_list;
          });
      })
      .push(function () {
        var i, div_list = gadget.element.querySelectorAll('.slapos-parameter-dict-key > div'),
          label_list = gadget.element.querySelectorAll('label.slapos-parameter-dict-key');

        // console.log("Collapse paramaters");

        for (i = 0; i < div_list.length; i = i + 1) {
          $(div_list[i]).hide();
        }

        for (i = 0; i < label_list.length; i = i + 1) {
          $(label_list[i]).addClass("slapos-parameter-dict-key-colapse");
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

    .declareMethod('render', function (options) {
      var parameter_hash = options.value.parameter.parameter_hash,
        // XXX Do we directly get parameter_xml parameter?
        parameter_xml = options.value.parameter.parameter_xml;

      if (parameter_hash !== undefined) {
        // A JSON where provided via gadgetfield
        parameter_xml = atob(parameter_hash);
      }

      return this.changeState({
        // Not used parameters
        // editable: options.editable,
        // hidden: options.hidden,
        // key: options.key,
        serialisation: options.serialisation,
        json_url: options.value.parameter.json_url,
        parameter_xml: parameter_xml,
        restricted_softwaretype: options.value.parameter.restricted_softwaretype,
        restricted_parameter: options.value.parameter.restricted_parameter,
        shared: options.value.parameter.shared,
        softwaretype: options.value.parameter.softwaretype,
        softwareindex: options.value.parameter.softwareindex,
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
        tag_name = evt.target.tagName;

      if ((tag_name === 'LABEL') &&
          (evt.target.className.indexOf("slapos-parameter-dict-key") !== -1)) {
        return collapseParameter(evt.target);
      }

      if (evt.target.className.indexOf("bt_close") !== -1) {
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
          (evt.target.className.indexOf("slapos-show-form") !== -1)) {
        return queue
          .push(function () {
            return showParameterForm(gadget);
          });
      }

      if ((tag_name === 'BUTTON') &&
          (evt.target.className.indexOf("slapos-show-raw-parameter") !== -1)) {
        return queue
          .push(function () {
            return showRawParameter(gadget);
          });
      }

      if ((tag_name === 'BUTTON') &&
          (evt.target.className.indexOf("add-sub-form") !== -1)) {
        return queue
          .push(function () {
            return addSubForm(gadget, evt.target);
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
          if (text_content !== null) {
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

    //.declareService(function () {
    //  var gadget = this;
      //return gadget.processValidation(gadget.options.json_url)
      //  .fail(function (error) {
      //    var parameter_xml = '';
      //    console.log(error.stack);
      //    if (gadget.options.value.parameter.parameter_hash !== undefined) {
      //      parameter_xml = atob(gadget.options.value.parameter.parameter_hash);
      //    }
      //    return gadget.renderFailoverTextArea(parameter_xml, error.toString())
      //      .push(function () {
      //        error = undefined;
      //        return gadget;
      //      });
      //  });
    //});

}(window, document, rJS, $, XMLSerializer, jQuery, vkbeautify,
  rJS.loopEventListener, domsugar, Boolean));