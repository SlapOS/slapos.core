/*jslint nomen: true, maxlen: 200, indent: 2, unparam: true*/
/*global window, rJS, domsugar, Boolean, btoa, atob */

(function (window, rJS, domsugar, Boolean, btoa, atob) {
  "use strict";

  function render_selection(json_field, default_value, is_required, editable) {
    var input,
      option_list = [domsugar('option', {
        value: "",
        selected: (default_value === undefined)
      })],
      option_index,
      selected,
      is_selected = (default_value === undefined),
      data_format = "string",
      property_dict = {
        size: 1,
        "placeholder": " ",
        "class": "slapos-parameter"
      };

    if (json_field.type === "integer" || json_field.type === "number") {
      data_format = "number";
    } else if (json_field.type === "boolean") {
      data_format = "boolean";
    }
    if (default_value === undefined) {
      default_value = "";
    }
    for (option_index in json_field['enum']) {
      if (json_field['enum'].hasOwnProperty(option_index)) {
        selected = (json_field['enum'][option_index].toString() === default_value.toString());
        is_selected = (is_selected || selected);
        option_list.push(domsugar('option', {
          value: json_field['enum'][option_index],
          text: json_field['enum'][option_index],
          "data-format": data_format,
          selected: selected
        }));
      }
    }
    if (!is_selected) {
      // The default value should be included even if it is
      // outside the enum.
      option_list.push(domsugar('option', {
        value: default_value,
        text: default_value,
        "data-format": data_format,
        selected: true
      }));
    }

    property_dict["data-format"] = data_format;
    if (is_required) {
      property_dict.required = true;
    }

    input = domsugar('select', property_dict, option_list);
    if (!editable) {
      input.classList.add("readonly");
      input["aria-disabled"] = "true";
      input["tab-index"] = "-1";
    }
    return input;
  }

  function render_selection_oneof(json_field, default_value, is_required, editable) {
    var input,
      option_list = [domsugar('option', {
        value: "",
        selected: (default_value === undefined)
      })],
      property_dict = {
        size: 1,
        "placeholder": " ",
        "class": "slapos-parameter"
      };

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
    if (is_required) {
      property_dict.required = true;
    }
    input = domsugar('select', property_dict, option_list);
    if (!editable) {
      input.classList.add("readonly");
      input["aria-disabled"] = "true";
      input["tab-index"] = "-1";
    }
    return input;
  }

  function render_textarea(json_field, default_value, data_format, is_required, editable) {
    var input, property_dict = {
      "data-format": data_format,
      "placeholder": " ",
      "class": "slapos-parameter"
    };
    if (default_value !== undefined) {
      if (default_value instanceof Array) {
        property_dict.value = default_value.join("\n");
      } else {
        property_dict.value = default_value;
      }
    }
    if (is_required) {
      property_dict.required = true;
    }
    input = domsugar('textarea', property_dict);
    if (!editable) {
      input.setAttribute('readonly', true);
    }
    return input;
  }



  function testInteger(value) {
    var parsed_value;
    if (value === undefined || value === "") {
      // Value is empty so it is ok to render the field
      return true;
    }
    parsed_value = parseFloat(value);
    if (!isNaN(parsed_value) && ((parsed_value % 1) === 0)) {
      return true;
    }
    return false;
  }

  function testNumber(value) {
    var parsed_value;
    if (value === undefined || value === "") {
      // Value is empty so it is ok to render the field
      return true;
    }
    parsed_value = parseFloat(value);
    if (!isNaN(parsed_value)) {
      return true;
    }
    return false;
  }

  function render_field(json_field, default_value, is_required, editable) {
    var input,
      data_format,
      domsugar_input_dict = {"placeholder": " ", "class": "slapos-parameter"};
    if (json_field['enum'] !== undefined) {
      return render_selection(json_field, default_value, is_required, editable);
    }

    if (json_field.oneOf !== undefined) {
      return render_selection_oneof(json_field, default_value, is_required, editable);
    }

    if (json_field.type === "boolean") {
      json_field['enum'] = [true, false];
      if (default_value === "true") {
        default_value = true;
      }
      if (default_value === "false") {
        default_value = false;
      }
      return render_selection(json_field, default_value, is_required, editable);
    }

    if (json_field.type === "array") {
      data_format = json_field.type;
      if (json_field.items !== undefined) {
        if (json_field.items.type === "number" || json_field.items.type === "integer") {
          data_format = "array-number";
        }
      }
      return render_textarea(json_field, default_value, data_format, is_required, editable);
    }

    if (json_field.type === "string" && json_field.textarea === true) {
      return render_textarea(json_field, default_value, "string", is_required, editable);
    }

    if (default_value !== undefined) {
      domsugar_input_dict.value = default_value;
    }

    if (json_field.type === "integer" && testInteger(default_value)) {
      domsugar_input_dict.type = "number";
    } else if (json_field.type === "number" && testNumber(default_value)) {
      domsugar_input_dict.type = "number";
      domsugar_input_dict.step = "any";
    } else if (json_field.type === "hidden") {
      domsugar_input_dict.type = "hidden";
    } else {
      domsugar_input_dict.type = "text";
    }

    if (is_required) {
      domsugar_input_dict.required = true;
    }
    input = domsugar('input', domsugar_input_dict);
    if (!editable) {
      input.setAttribute('readonly', true);
    }
    return input;
  }

  function render_subform(json_field, default_dict, root, path, editable) {
    var div_input,
      key,
      div,
      label,
      input,
      default_value,
      default_used_list = [],
      is_required;

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

        if (editable) {
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
            if (editable) {
              label = domsugar('label', {
                text: default_value,
                'class': "slapos-parameter-dict-key slapos-parameter-dict-key-colapse"
              }, [
                domsugar('span', {
                  text: "×",
                  "class": "bt_close CLOSE" + path + "/" + default_value,
                  title: "Remove this parameter section."
                })
              ]);
            } else {
              label = domsugar('label', {
                text: default_value,
                'class': "slapos-parameter-dict-key slapos-parameter-dict-key-colapse"
              });
            }

            div.appendChild(render_subform(
              json_field.patternProperties['.*'],
              default_dict[default_value],
              domsugar("div", {
                "class": "slapos-parameter-dict-key"
              }, [label]),
              path + "/" + default_value,
              editable
            ));
          }
        }
        root.appendChild(div);

        return div;
      }
    }

    // Expand by force the allOf recomposing the properties and required.
    for (key in json_field.allOf) {
      if (json_field.allOf.hasOwnProperty(key)) {
        if (json_field.properties === undefined) {
          json_field.properties = json_field.allOf[key].properties;
        } else if (json_field.allOf[key].properties !== undefined) {
          json_field.properties = Object.assign({},
              json_field.properties,
              json_field.allOf[key].properties
            );
        }
        if (json_field.required === undefined) {
          json_field.required = json_field.allOf[key].required;
        } else if (json_field.allOf[key].required !== undefined) {
          json_field.required.push.apply(
            json_field.required,
            json_field.allOf[key].required
          );
        }
      }
    }

    for (key in json_field.properties) {
      if (json_field.properties.hasOwnProperty(key)) {
        if (editable || default_dict[key] !== undefined) {
          label = domsugar("label", {
            'text': json_field.properties[key].title
          });
          is_required = false;
          if ((Array.isArray(json_field.required)) && (json_field.required.includes(key))) {
            is_required = true;
          }
          if (json_field.properties[key].type === 'object') {
            label.setAttribute("class", "slapos-parameter-dict-key slapos-parameter-dict-key-collapse");
            div_input = render_subform(json_field.properties[key],
              default_dict[key],
              domsugar("div", {"class": "input"}),
              path + "/" + key,
              editable);
          } else {
            input = render_field(
              json_field.properties[key],
              default_dict[key],
              is_required,
              editable
            );
            input.name = path + "/" + key;
            div_input = domsugar("div", {"class": "input"}, [input]);
          }
          default_used_list.push(key);
          if (json_field.properties[key]['default'] !== undefined) {
            div_input.appendChild(
              domsugar("span",
                {'text': '(default = ' + json_field.properties[key]['default'] + ')'})
            );
          }
          div_input.appendChild(domsugar("span", {'class': 'error'}));
          root.appendChild(
            domsugar("div", {
              "class": "subfield",
              title: json_field.properties[key].description
            }, [label, div_input])
          );
        }
      }
    }
    for (key in default_dict) {
      if (default_dict.hasOwnProperty(key)) {
        if (default_used_list.indexOf(key) < 0) {
          if (typeof default_dict[key] === 'object') {
            div = domsugar("div", {title: key}, [
              domsugar("label", {
                text: key,
                "class": "slapos-parameter-dict-key slapos-parameter-dict-key-colapse"
              }),
              render_subform({},
                default_dict[key],
                domsugar("div", {"class": "input"}),
                path + "/" + key,
                editable)
            ]);
          } else {
            input = render_field({"type": "string", "textarea": true}, default_dict[key], false, editable);
            input.name = path + "/" + key;
            div = domsugar("div", {
              title: key,
              "class": "subfield"
            }, [
              domsugar("label", {text: key}),
              domsugar("div", {"class": "input"}, [
                input,
                domsugar("span", {text: '(Not part of the schema)'}),
                domsugar("span", {'class': 'error'})
              ])
            ]);
          }
          default_used_list.push(key);
          root.appendChild(div);
        }
      }
    }
    return root;
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

    div = render_subform(subform_json, {}, div, element.name + "/" + input_text.value, gadget.state.editable);
    element.parentNode.parentNode.insertBefore(div, element.parentNode.parentNode.children[1]);
    return div;
  }

  /////////////////////////////////////////////////////
  // Gadget methods
  /////////////////////////////////////////////////////
  rJS(window)
    .declareMethod("validateJSON", function (schema_url, generated_json) {
      return this.getDeclaredGadget('json_form_load_schema')
        .push(function (gadget) {
          if (schema_url === undefined) {
            // Skip validation if no schema is provided.
            return {errors: []};
          }
          return gadget.validateJSON(undefined, schema_url, generated_json);
        });
    })
    .declareMethod('render', function (options) {
      return this.changeState({
        schema_url: options.schema_url,
        json_field: options.json_field,
        default_dict: options.default_dict,
        editable: options.editable,
        // Force refresh in any case
        render_timestamp: new Date().getTime()
      });
    })
    .onStateChange(function () {
      var gadget = this,
        i,
        div = render_subform(
          gadget.state.json_field,
          gadget.state.default_dict,
          domsugar('div'),
          undefined,
          gadget.state.editable
        ),
        div_list = div.querySelectorAll('.slapos-parameter-dict-key > div');

      for (i = 0; i < div_list.length; i = i + 1) {
        // This should be replaced by a proper class hidden-div
        div_list[i].classList.add('display-none');
      }
      if (div.hasChildNodes()) {
        div.classList.add("slap_json_form");
      }

      return domsugar(gadget.element, {}, [div]);
    })
    .onEvent("change", function (evt) {
      var gadget = this;

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
          (evt.target.className.indexOf("add-sub-form") !== -1)) {
        return queue
          .push(function () {
            return addSubForm(gadget, evt.target);
          });
      }
    }, false, false)

    .declareMethod('getContent', function () {
      var gadget = this,
        json_dict = getFormValuesAsJSONDict(gadget.element);
      return gadget.validateJSON(gadget.state.schema_url, json_dict)
        .push(function (validation) {
          var error_index,
            field_name,
            div,
            input_field,
            error_dict;
          gadget.element.querySelectorAll("span.error").forEach(function (span, i) {
            span.textContent = "";
          });
          gadget.element.querySelectorAll("div.error-input").forEach(function (div, i) {
            div.setAttribute("class", "");
          });
          // Update fields if errors exist
          for (error_index in validation.errors) {
            if (validation.errors.hasOwnProperty(error_index)) {
              error_dict = validation.errors[error_index];
              // error_dict = { error : "", instanceLocation: "#", keyword: "", keywordLocation: "" }
              field_name = error_dict.instanceLocation.slice(1);
              if (field_name !== "") {
                input_field = gadget.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
                if (input_field === null) {
                  field_name = field_name.split("/").slice(0, -1).join("/");
                  input_field = gadget.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
                }
                if (input_field !== null) {
                  div = input_field.parentNode;
                  div.setAttribute("class", "slapos-parameter error-input");
                  div.querySelector("span.error").textContent = validation.errors[error_index].error;
                }
              } else if (error_dict.keyword === "required") {
                // Specific use case for required
                field_name = "/" + error_dict.key;
                input_field = gadget.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
                if (input_field === null) {
                  field_name = field_name.split("/").slice(0, -1).join("/");
                  input_field = gadget.element.querySelector(".slapos-parameter[name='/" + field_name  + "']");
                }
                if (input_field !== null) {
                  div = input_field.parentNode;
                  div.setAttribute("class", "slapos-parameter error-input");
                  div.querySelector("span.error").textContent = error_dict.error;
                }
              }
            }
          }
          return json_dict;
        });
    }, {mutex: 'statechange'});

}(window, rJS, domsugar, Boolean, btoa, atob));
