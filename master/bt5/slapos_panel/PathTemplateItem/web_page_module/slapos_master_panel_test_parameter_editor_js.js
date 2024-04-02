/*jslint indent: 2, maxerr: 3, maxlen: 80 */
/*global window, rJS, RSVP */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("getTranslationDict", "getTranslationDict")
    .declareMethod('triggerSubmit', function () {
      var argument_list = arguments;
      return this.getDeclaredGadget('access')
        .push(function (access_gadget) {
          return access_gadget.triggerSubmit.call(access_gadget, argument_list);
        });
    })
    .declareMethod('render', function (options) {
      return new RSVP.Queue(RSVP.hash({
        access_gadget: this.getDeclaredGadget('access'),
        translation_dict: this.getTranslationDict([
          'Parameter Test'
        ])
      }))
        .push(function (result_dict) {
          return result_dict.access_gadget.render(options, [{
            title: result_dict.translation_dict['Parameter Test'],
            jio_key: 'software_product_module',
            erp5_action: 'slapos_parameter_editor_test_view'
          }]);
        });
    });

}(window, rJS, RSVP));
