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
          'Services',
          'Request',
          'Projects',
          'Servers',
          'Tickets',
          'Invoices',
          'Pay'
        ])
      }))
        .push(function (result_dict) {
          return result_dict.access_gadget.render(options, [{
            title: result_dict.translation_dict.Services,
            jio_key: 'instance_tree_module',
            erp5_action: 'slapos_panel_view_my_instance_tree_list'
          }, {
            title: result_dict.translation_dict.Request,
            jio_key: 'instance_tree_module',
            erp5_action: 'request_slapos_payable_instance_tree'
          }, {
            title: result_dict.translation_dict.Projects,
            jio_key: 'project_module',
            erp5_action: 'slapos_panel_view_my_project_list'
          }, {
            title: result_dict.translation_dict.Servers,
            jio_key: 'compute_node_module',
            erp5_action: 'slapos_panel_view_my_compute_node_list'
          }, {
            title: result_dict.translation_dict.Tickets,
            jio_key: 'support_request_module',
            erp5_action: 'slapos_panel_view_my_ticket_list'
          }, {
            title: result_dict.translation_dict.Invoices,
            jio_key: 'accounting_module',
            erp5_action: 'slapos_panel_view_my_invoice_list'
          }, {
            title: result_dict.translation_dict.Pay,
            jio_key: 'accounting_module',
            erp5_action: 'pay_my_slapos_sale_invoice_transaction'
          }]);
        });
    });

}(window, rJS, RSVP));
