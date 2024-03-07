/*jslint nomen: true, maxlen: 200, indent: 2*/
/*global window, rJS, RSVP, btoa, URI, Validator, jIO, JSON, $RefParser */
(function (window, rJS, RSVP, btoa, URI, Validator, jIO, JSON, $RefParser) {
  "use strict";

  function getJSON(url) {
    var uri = URI(url),
      headers = {},
      protocol = uri.protocol();
    if (protocol === "http" && URI(window.location).protocol() === "https") {
      throw new Error("You cannot load http JSON in https page");
    }
    if (protocol === "http" || protocol === "https") {
      if (uri.username() !== "" && uri.password() !== "") {
        headers = {
          Authorization: "Basic " + btoa(uri.username() + ":" + uri.password())
        };
      }
    }
    return new RSVP.Queue()
      .push(function () {
        return jIO.util.ajax({
          url: url,
          headers: headers
        })
          .then(function (evt) {
            return evt.target.responseText;
          });
      });
  }

  rJS(window)
    .declareMethod("loadJSONSchema", function (url, serialisation) {
      var meta_schema_url = "slapos_load_meta_schema.json";

      if (serialisation === "xml") {
        meta_schema_url = "slapos_load_meta_schema_xml.json";
      }

      if (serialisation === "json-in-xml") {
        meta_schema_url = "slapos_load_meta_schema_json_in_xml.json";
      }
      return getJSON(meta_schema_url)
        .push(function (meta_schema) {
          return new RSVP.Queue()
            .push(function () {
              return $RefParser.dereference(url);
            })
            .push(function (schema) {
              var validator = new Validator(JSON.parse(meta_schema), '7');
              if (!validator.validate(schema)) {
                throw new Error("Non valid JSON schema " + JSON.stringify(schema));
              }
              return schema;
            });
        });
    })
    .declareMethod("loadSoftwareJSON", function (url) {
      return getJSON(url)
        .push(function (software_cfg_json) {
          return new RSVP.Queue()
            .push(function () {
              return $RefParser
                .dereference("slapos_load_software_schema.json");
            })
            .push(function (software_schema) {
              var software_json = JSON.parse(software_cfg_json),
                validator = new Validator(software_schema, '7');
              if (!validator.validate(software_json)) {
                throw new Error("Non valid JSON for software.cfg.json:" + software_cfg_json);
              }
              return software_json;
            });
        });
    });
}(window, rJS, RSVP, btoa, URI, Validator, jIO, JSON, $RefParser));