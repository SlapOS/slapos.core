# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, simulate

import transaction


class TestSlapOSAccountingInteractionWorkflow(SlapOSTestCaseMixin):
  def beforeTearDown(self):
    transaction.abort()

  @simulate('Delivery_calculate',
            '*args, **kwargs',
            """# Script body
portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by Delivery_calculate')
            """)
  def _test_calculate(self, new_id, newContent, **new_kw):
    cancel_spl = newContent(**new_kw)
    close_spl = newContent(**new_kw)
    confirm_spl = newContent(**new_kw)
    deliver_spl = newContent(**new_kw)
    deliver_spl.confirm()
    deliver_spl.stop()
    order_spl = newContent(**new_kw)
    plan_spl = newContent(**new_kw)
    setReady_spl = newContent(**new_kw)
    setReady_spl.confirm()
    start_spl = newContent(**new_kw)
    start_spl.confirm()
    stop_spl = newContent(**new_kw)
    stop_spl.confirm()
    submit_spl = newContent(**new_kw)

    cancel_spl.cancel()
    close_spl.close()
    confirm_spl.confirm()
    deliver_spl.deliver()
    order_spl.order()
    plan_spl.plan()
    setReady_spl.setReady()
    start_spl.start()
    stop_spl.stop()
    submit_spl.submit()

    self.assertEqual(
      cancel_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      close_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      confirm_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      deliver_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      order_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      plan_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      setReady_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      start_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      stop_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')
    self.assertEqual(
      submit_spl.workflow_history['edit_workflow'][-1]['comment'],
      'Visited by Delivery_calculate')

  def test_SalePackingList_calculate(self):
    new_id = self.generateNewId()
    newContent = self.portal.sale_packing_list_module.newContent
    portal_type = "Sale Packing List"
    self._test_calculate(new_id, newContent, portal_type=portal_type)

  def test_SaleInvoiceTransaction_calculate(self):
    new_id = self.generateNewId()
    newContent = self.portal.accounting_module.newContent
    portal_type = "Sale Invoice Transaction"
    self._test_calculate(new_id, newContent, portal_type=portal_type,
        start_date='2011/01/01')
