/*jslint indent: 2, maxerr: 3, maxlen: 80 */
/*global window, rJS, RSVP */
(function (window, rJS, RSVP) {
  "use strict";

  rJS(window)
    .declareAcquiredMethod("getTranslationDict", "getTranslationDict")
    .declareMethod('render', function (options) {
      return new RSVP.Queue(RSVP.hash({
        access_gadget: this.getDeclaredGadget('access'),
        translation_dict: this.getTranslationDict([
          'Home',
          'Ticket Activity',
          'User Usage',
          'Instance Errors'
        ])
      }))
        .push(function (result_dict) {
          return result_dict.access_gadget.render(options, [{
            title: result_dict.translation_dict.Home,
            jio_key: 'web_page_module/slapos_admin_front_page',
            erp5_action: 'render'
          }, {
            title: result_dict.translation_dict['User Usage'],
            jio_key: 'instance_tree_module',
            erp5_action: 'slapos_resilience_usage_report'
          }, {
            title: result_dict.translation_dict['Instance Errors'],
            jio_key: 'support_request_module',
            erp5_action: 'slapos_support_request_instance_message_report'
          }, {
            title: result_dict.translation_dict['Ticket Activity'],
            jio_key: 'compute_node_module',
            erp5_action: 'slapos_ticket_activity_report'
          }]);
        });
    });

}(window, rJS, RSVP));
