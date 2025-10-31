/*globals window, document, RSVP, rJS, XMLHttpRequest, URL,
          history, console */
/*jslint indent: 2, maxlen: 80*/
(function () {
  "use strict";

  function callJsonRpcEntryPoint(url, data) {
    if (data === undefined) {
      data = {};
    }
    return RSVP.Queue(jIO.util.ajax({
      url: url,
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
    } catch {
      // Return an url which will always fail
      // to force the gadget to render the textarea
      json_url = 'http://0.0.0.0';
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

  rJS(window)
    .allowPublicAcquisition('notifyChange', function () {
      // Does nothing
      return;
    })

    .declareService(function () {
      // A service is triggered when this gadget is added to the DOM
      return this.fetchDataFromSlapProxy();
    })
    .declareMethod('fetchDataFromSlapProxy', function () {
      var gadget = this;
      ////////////////////////////////////////////////////////////////
      // First, get the list (expecting length 1) of compute node
      ////////////////////////////////////////////////////////////////
      return callJsonRpcEntryPoint('../slapos.get.v0.hateoas_url')
        .push(function (json_response) {
          return callHateoasEntryPoint(json_response.hateoas_url);
        })
        .push(function (json_response) {
          return callHateoasEntryPoint(json_response._links.raw_search.href, {
            query: 'portal_type:"Compute Node" AND validation_state:validated'
          });
        })
        .push(function (json_response) {
          var compute_node_list = json_response._embedded.contents;
          if (compute_node_list.length !== 1) {
            throw new Error(compute_node_list.length + ' compute node found. Expected 1 only.');
          }
          return compute_node_list[0].reference;
        })

        ////////////////////////////////////////////////////////////////
        // Second, get the list (expecting length 1) of software instance
        ////////////////////////////////////////////////////////////////
        .push(function (computer_guid) {
          return callJsonRpcEntryPoint('/slapos.allDocs.v0.compute_node_instance_list', {
            computer_guid: computer_guid
          });
        })
        .push(function (json_response) {
          var instance_list = json_response.result_list;
          if (instance_list.length !== 1) {
            throw new Error(instance_list.length + ' software instance found. Expected 1 only.');
          }
          return instance_list[0].instance_guid;
        })

        ////////////////////////////////////////////////////////////////
        // Third, get the software instance info
        ////////////////////////////////////////////////////////////////
        .push(function (instance_guid) {
          return callJsonRpcEntryPoint('/slapos.get.v0.software_instance', {
            instance_guid: instance_guid
          });
        })
        .push(function (json_response) {
          // Assert, as JSON api in slapproxy only support the top instance
          if (json_response.title !== json_response.root_instance_title) {
            throw new Error('Only the top instance is supported');
          }

          return RSVP.hash({
            json_response: json_response,
            json_url: guessSoftwareReleaseJsonUrl(json_response.software_release_uri)
          });

        })
        .push(function (result_hash) {
          var xml_document = document.implementation.createDocument(
            null,
            'instance'
          ),
            key,
            xml_element,
            parameter_xml,
            json_response = result_hash.json_response;

          document.querySelector("#slapproxy_header_title").textContent =
          "Software Instance: " + json_response.title + " (offline)";

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
  
          return gadget.changeState({
            title: json_response.title,
            software_release_uri: json_response.software_release_uri,
            json_url: result_hash.json_url,
            shared: json_response.shared,
            software_type: json_response.software_type,
            parameter_xml: parameter_xml,
            sla_parameters: json_response.sla_parameters,
            editable: true,
          });
        });
    })

    .onStateChange(function () {
      var gadget = this;
      return gadget.getDeclaredGadget('field_your_instance_xml')
        .push(function (sub_gadget) {
          return sub_gadget.render({
            json_url: gadget.state.json_url,
            shared: gadget.state.shared,
            softwaretype: gadget.state.software_type,
            parameter_xml: gadget.state.parameter_xml,
            restricted_softwaretype: true,
            editable: gadget.state.editable,
          });
        });
    })
    .onEvent('submit', function () {
      var gadget = this;
      if (gadget.state.editable !== true) {
        return;
      }
      return gadget.getDeclaredGadget('field_your_instance_xml')
        .push(function (sub_gadget) {
          return sub_gadget.getContent();
        })
        .push(function (sub_gadget_content) {

          var xml_document = rJS.parseDocumentStringOrFail(
            sub_gadget_content.text_content,
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
            title: gadget.state.title,
            software_release_uri: gadget.state.software_release_uri,
            software_type: sub_gadget_content.software_type,
            shared: gadget.state.shared,
            state: gadget.state.state,
            parameters: json_document,
            sla_parameters: gadget.state.sla_parameters,
          });
        });
    }, false, true);

}());