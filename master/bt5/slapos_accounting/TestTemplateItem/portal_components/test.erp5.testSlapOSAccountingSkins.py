# -*- coding: utf8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, withAbort, simulate

from zExceptions import Unauthorized
from DateTime import DateTime
import time

class TestSlapOSAccounting(SlapOSTestCaseMixin):

  def createInstanceTree(self):
    new_id = self.generateNewId()
    return self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title="Subscription %s" % new_id,
      reference="TESTHS-%s" % new_id,
      )

  def createOpenSaleOrder(self):
    new_id = self.generateNewId()
    return self.portal.open_sale_order_module.newContent(
      portal_type='Open Sale Order',
      title="OpenSaleOrder %s" % new_id,
      reference="TESTOSO-%s" % new_id,
      )

  @withAbort
  def test_IT_calculateSubscriptionStartDate_REQUEST_disallowed(self):
    item = self.createInstanceTree()
    self.assertRaises(
      Unauthorized,
      item.InstanceTree_calculateSubscriptionStartDate,
      REQUEST={})

  @withAbort
  def test_IT_calculateSubscriptionStartDate_noWorkflow(self):
    item = self.createInstanceTree()
    item.workflow_history['instance_slap_interface_workflow'] = []
    date = item.InstanceTree_calculateSubscriptionStartDate()
    self.assertEqual(date, item.getCreationDate().earliestTime())

  @withAbort
  def test_IT_calculateSubscriptionStartDate_withRequest(self):
    item = self.createInstanceTree()
    item.workflow_history['instance_slap_interface_workflow'] = [{
        'comment':'Directly request the instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': DateTime('2012/11/15 11:11'),
        'action': 'request_instance'
        }]
    date = item.InstanceTree_calculateSubscriptionStartDate()
    self.assertEqual(date, DateTime('2012/11/15'))

  @withAbort
  def test_IT_calculateSubscriptionStartDate_withRequestEndOfMonth(self):
    item = self.createInstanceTree()
    item.workflow_history['instance_slap_interface_workflow'] = [{
        'comment':'Directly request the instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': DateTime('2012/11/30 11:11'),
        'action': 'request_instance'
    }]
    date = item.InstanceTree_calculateSubscriptionStartDate()
    self.assertEqual(date, DateTime('2012/11/30'))

  @withAbort
  def test_IT_calculateSubscriptionStartDate_withRequestAfterDestroy(self):
    item = self.createInstanceTree()
    destroy_date = DateTime('2012/10/30 11:11')
    request_date = DateTime('2012/11/30 11:11')
    item.workflow_history['instance_slap_interface_workflow'] = []
    item.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly destroy',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_date,
        'action': 'request_destroy'
    })
    item.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly request the instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': request_date,
        'action': 'request_instance'
    })
    date = item.InstanceTree_calculateSubscriptionStartDate()
    self.assertEqual(date, DateTime('2012/10/30'))

  @withAbort
  def test_IT_calculateSubscriptionStopDate_REQUEST_disallowed(self):
    item = self.createInstanceTree()
    self.assertRaises(
      Unauthorized,
      item.InstanceTree_calculateSubscriptionStopDate,
      REQUEST={})

  @withAbort
  def test_IT_calculateSubscriptionStopDate_withDestroy(self):
    item = self.createInstanceTree()
    destroy_date = DateTime('2012/10/30')
    item.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Directly destroy',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_date,
        'action': 'request_destroy'
    })
    date = item.InstanceTree_calculateSubscriptionStopDate()
    self.assertEqual(date, DateTime('2012/10/31'))

  @withAbort
  def test_IT_calculateSubscriptionStopDate_noDestroy(self):
    item = self.createInstanceTree()
    item.workflow_history['instance_slap_interface_workflow'] = []
    date = item.InstanceTree_calculateSubscriptionStopDate()
    self.assertEqual(date, None)

  def test_OpenSaleOrder_reindexIfIndexedBeforeLine_no_line(self):
    portal = self.portal
    order = self.createOpenSaleOrder()
    self.tic()
    indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    order.OpenSaleOrder_reindexIfIndexedBeforeLine()
    self.tic()
    new_indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    self.assertEqual(new_indexation_timestamp,
                      indexation_timestamp)

  def test_OpenSaleOrder_reindexIfIndexedBeforeLine_line_indexed_after(self):
    portal = self.portal
    order = self.createOpenSaleOrder()
    line = order.newContent(portal_type="Open Sale Order Line")
    self.tic()
    line.activate().immediateReindexObject()
    # XXX One more kitten killed
    time.sleep(1)
    self.tic()
    indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    order.OpenSaleOrder_reindexIfIndexedBeforeLine()
    self.tic()
    new_indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    self.assertNotEqual(new_indexation_timestamp,
                         indexation_timestamp)

  def test_OpenSaleOrder_reindexIfIndexedBeforeLine_line_indexed_before(self):
    portal = self.portal
    order = self.createOpenSaleOrder()
    order.newContent(portal_type="Open Sale Order Line")
    self.tic()
    order.activate().immediateReindexObject()
    # XXX One more kitten killed
    time.sleep(1)
    self.tic()
    indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    order.OpenSaleOrder_reindexIfIndexedBeforeLine()
    self.tic()
    new_indexation_timestamp = portal.portal_catalog(
      uid=order.getUid(),
      select_dict={'indexation_timestamp': None})[0].indexation_timestamp
    self.assertEqual(new_indexation_timestamp,
                      indexation_timestamp)

  def test_OpenSaleOrder_reindexIfIndexedBeforeLine_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.OpenSaleOrder_reindexIfIndexedBeforeLine,
      REQUEST={})


  @simulate("SaleInvoiceTransaction_createReversalPayzenTransaction", 
            "*args, **kwargs",  """context.portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SaleInvoiceTransaction_createReversalPayzenTransaction')
return context.getParentValue()""")
  def test_SaleInvoiceTransaction_createSlapOSReversalTransaction_payzen(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="payzen")

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createSlapOSReversalTransaction()
    self.assertTrue(redirect.endswith('accounting_module?portal_status_message=Reversal%20Transaction%20created.'), 
      "%s doesn't end with sale_invoice_transaction.SaleInvoiceTransaction_createSlapOSReversalTransaction()" % redirect)
    self.assertEqual(
        'Visited by SaleInvoiceTransaction_createReversalPayzenTransaction',
        sale_invoice_transaction.workflow_history['edit_workflow'][-1]['comment'])

  @simulate("SaleInvoiceTransaction_createReversalWechatTransaction", 
            "*args, **kwargs",  """context.portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SaleInvoiceTransaction_createReversalWechatTransaction')
return context.getParentValue()""")
  def test_SaleInvoiceTransaction_createSlapOSReversalTransaction_wechat(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="wechat")

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createSlapOSReversalTransaction()
    self.assertTrue(redirect.endswith('accounting_module?portal_status_message=Reversal%20Transaction%20created.'), 
      "%s doesn't end with sale_invoice_transaction.SaleInvoiceTransaction_createSlapOSReversalTransaction()" % redirect)
    self.assertEqual(
        'Visited by SaleInvoiceTransaction_createReversalWechatTransaction',
        sale_invoice_transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_SaleInvoiceTransaction_createSlapOSReversalTransaction_unknown(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="unknown")

    redirect = sale_invoice_transaction.SaleInvoiceTransaction_createSlapOSReversalTransaction()

    self.assertTrue(redirect.endswith('%s?portal_status_message=The%%20payment%%20mode%%20is%%20unsupported.' % sale_invoice_transaction.getRelativeUrl()), 
      "%s doesn't end with %s?portal_status_message=The%%20payment%%20mode%%20is%%20unsupported." % (redirect, sale_invoice_transaction.getRelativeUrl()))

  def test_SaleInvoiceTransaction_resetPaymentMode(self):
    sale_invoice_transaction = self.portal.accounting_module.newContent(portal_type="Sale Invoice Transaction")
    sale_invoice_transaction.edit(payment_mode="unknown",
      start_date=DateTime(),
      stop_date=DateTime())
    sale_invoice_transaction.confirm()
    sale_invoice_transaction.start( )
    sale_invoice_transaction.stop()

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), "unknown")
    sale_invoice_transaction.edit(payment_mode="payzen")

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), None)
    sale_invoice_transaction.edit(payment_mode="wechat")

    sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode()
    self.assertEqual(sale_invoice_transaction.getPaymentMode(), None)

    self.assertRaises(
      Unauthorized,
      sale_invoice_transaction.SaleInvoiceTransaction_resetPaymentMode,
      REQUEST={})

  def test_Person_get_set_AggregatedDelivery(self):
    person = self.makePerson()

    self.assertEqual(
      person.Person_getAggregatedDelivery(), None)

    delivery = self.portal.sale_packing_list_module.newContent(
      portal_type="Sale Packing List")

    person.Person_setAggregatedDelivery(delivery)


    self.assertEqual(delivery,
      person.Person_getAggregatedDelivery())

  def test_AccountingTransactionModule_getUnpaidInvoiceList(self):
    person = self.makePerson(user=1)
  
    template = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredDefaultPrePaymentSubscriptionInvoiceTemplate())
    current_invoice = template.Base_createCloneDocument(batch_mode=1)

    current_invoice.edit(
        destination_value=person,
        destination_section_value=person,
        destination_decision_value=person,
        start_date=DateTime('2019/10/20'),
        stop_date=DateTime('2019/10/20'),
        title='Fake Invoice for Demo User Functional',
        price_currency="currency_module/EUR",
        reference='1')

    cell = current_invoice["1"]["movement_0"]
    cell.edit(quantity=1)
    cell.setPrice(1)
    
    current_invoice.plan()
    current_invoice.confirm()
    current_invoice.startBuilding()
    current_invoice.reindexObject()
    current_invoice.stop()

    self.tic()
    current_invoice.Delivery_manageBuildingCalculatingDelivery()
    self.tic()
    current_invoice.SaleInvoiceTransaction_forceBuildSlapOSAccountingLineList()

    self.tic()
    self.login(person.getUserId())
    unpaid_invoice_list = self.portal.accounting_module.AccountingTransactionModule_getUnpaidInvoiceList()
    self.assertEqual(
      [i.getRelativeUrl() for i in unpaid_invoice_list],
      [current_invoice.getRelativeUrl()])

    self.login()
    payment_template = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredDefaultPrePaymentTemplate())
    payment = payment_template.Base_createCloneDocument(batch_mode=1)

    for line in payment.contentValues():
      if line.getSource() == "account_module/payment_to_encash":
        line.setQuantity(-1)
      elif line.getSource() == "account_module/receivable":
        line.setQuantity(1)

    payment.confirm()
    payment.start()
    payment.setCausalityValue(current_invoice)
    payment.setDestinationSectionValue(person)
    
    payment.stop()
    self.tic()

    is_lettered = False
    letter = None
    for line in current_invoice.contentValues():
      if line.getSource() == "account_module/receivable":
        is_lettered = True
        letter = line.getGroupingReference()

    self.assertTrue(is_lettered)

    # is it groupped?
    is_lettered = False
    for line in payment.contentValues():
      if line.getSource() == "account_module/receivable":
        is_lettered = True
        self.assertEqual(letter, line.getGroupingReference())
    
    self.assertTrue(is_lettered)
 
    self.login(person.getUserId())
    unpaid_invoice_list = self.portal.accounting_module.AccountingTransactionModule_getUnpaidInvoiceList()
    self.assertEqual(
      [i.getRelativeUrl() for i in unpaid_invoice_list],
      [])