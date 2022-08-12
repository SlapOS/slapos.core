/*global window, rJS, RSVP, domsugar, jIO, console */
/*jslint nomen: true, maxlen:80, indent:2*/
(function (window, rJS, RSVP, domsugar, jIO, console) {
  "use strict";

  var DISPLAY_URL = 'display_url',
    FIELD_SCOPE = 'url_input';

  function renderSoftwareReleaseURLView(gadget) {
    return gadget.declareGadget('gadget_html5_input.html', {scope: FIELD_SCOPE})
      .push(function (sub_gadget) {
        return sub_gadget.render({
          value: gadget.state.value,
          editable: gadget.state.editable,
          required: gadget.state.required,
          id: gadget.state.key,
          name: gadget.state.key,
          type: 'url'
        })
          .push(function () {
            domsugar(gadget.element, [
              sub_gadget.element
            ]);
          });
      });
  }

  function filterUnique(value, index, self) {
    return self.indexOf(value) === index;
  }

  function getContentFromSoftwareReleaseURLView(gadget) {
    var software_url;
    return gadget.getDeclaredGadget(FIELD_SCOPE)
      .push(function (sub_gadget) {
        return sub_gadget.getContent();
      })
      .push(function (result) {
        software_url = result[gadget.state.key];
        return jIO.util.ajax({
          url: software_url + '.json',
          dataType: 'json'
        });
      })
      .push(function (evt) {
        var software_json = evt.target.response,
          software_type_array = [],
          software_type,
          result = {};
        console.log(software_json);
        for (software_type in software_json['software-type']) {
          if (software_json['software-type'].hasOwnProperty(software_type)) {
            // Multiple form can use the same software type
            // This is a hack to separate slave/non slave
            if (software_json['software-type'][software_type]
                .hasOwnProperty('software-type')) {
              software_type_array.push(
                software_json['software-type'][software_type]['software-type']
              );
            } else {
              software_type_array.push(software_type);
            }
          }
        }
        result[gadget.state.title_key] = software_json.name;
        result[gadget.state.description_key] = software_json.description || "";
        result[gadget.state.software_release_key] = software_url;
        result[gadget.state.software_type_key] =
          software_type_array.filter(filterUnique);
        console.log(result);
        return result;
      });
  }

  rJS(window)
    .declareMethod('render', function (options) {
      console.log(options);
      return this.changeState({
        display_step: DISPLAY_URL,
        value: options.value,
        editable: options.editable,
        // required is not a gadget field parameter. TOFIX
        required: true,//options.required,
        key: options.key,
        title_key: options.title_key,
        description_key: options.description_key,
        software_release_key: options.software_release_key,
        software_type_key: options.software_type_key
      });
    })

    .onStateChange(function (modification_dict) {
      var gadget = this;

      if (modification_dict.display_step === DISPLAY_URL) {
        return renderSoftwareReleaseURLView(gadget);
      }

      if (modification_dict.hasOwnProperty('display_step')) {
        throw new Error('Unhandled display step: ' + gadget.state.display_step);
      }
    })

    //////////////////////////////////////////////////
    // Used when submitting the form
    //////////////////////////////////////////////////
    .declareMethod('getContent', function () {
      console.log('getContent');
      var gadget = this,
        display_step = gadget.state.display_step,
        queue;

      if (gadget.state.display_step === DISPLAY_URL) {
        queue = new RSVP.Queue(getContentFromSoftwareReleaseURLView(gadget));
      } else {
        throw new Error('getContent form not handled: ' + display_step);
      }

      return queue;
    }, {mutex: 'changestate'})

    .declareAcquiredMethod("notifyValid", "notifyValid")
    .declareAcquiredMethod("notifyInvalid", "notifyInvalid")
    .declareMethod('checkValidity', function () {
      var gadget = this,
        result;
      // XXX Cache getContent result (to prevent doing 2 ajax queries)
      return new RSVP.Queue(getContentFromSoftwareReleaseURLView(gadget))
        .push(function () {
          result = true;
          return gadget.notifyValid();
        }, function (error) {
          result = false;
          console.warn(error);
          return gadget.notifyInvalid('Can not extract software release json');
        })
        .push(function () {
          return result;
        });
    }, {mutex: 'changestate'});

}(window, rJS, RSVP, domsugar, jIO, console));