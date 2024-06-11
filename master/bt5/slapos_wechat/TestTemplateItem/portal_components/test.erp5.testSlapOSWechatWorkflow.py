# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2018 Nexedi SA and Contributors. All Rights Reserved.
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
from erp5.component.test.testSlapOSWechatSkins import TestSlapOSWechatMixin
from erp5.component.document.WechatService import WechatService


from DateTime import DateTime
from Products.ERP5Type.tests.utils import createZODBPythonScript
import transaction

HARDCODED_PRICE = 99.6

class TestSlapOSWechatInterfaceWorkflow(TestSlapOSWechatMixin):

  def _simulatePaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\nreturn -%f' % HARDCODED_PRICE)

  def _dropPaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)

  def test_generateManualPaymentPage_noAccountingTransaction(self):
    event = self.createWechatEvent()
    self.assertRaises(AttributeError, event.generateManualPaymentPage)

  def test_generateManualPaymentPage_registeredTransaction(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    _ , _ = payment.PaymentTransaction_generateWechatId()
    self.assertRaises(ValueError, event.generateManualPaymentPage)

  def test_generateManualPaymentPage_noPaymentService(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    self.assertRaises(AttributeError, event.generateManualPaymentPage)

  def test_generateManualPaymentPage_noCurrency(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource_value=None
    )
    event.edit(
      destination_value=payment,
      source=self.wechat_secure_payment.getRelativeUrl(),
    )
    self.assertRaises(AttributeError, event.generateManualPaymentPage)

  def test_generateManualPaymentPage_defaultUseCase(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource="currency_module/CNY",
    )
    event.edit(
      destination_value=payment,
      source=self.wechat_secure_payment.getRelativeUrl(),
    )

    payment_transaction_id = payment.getId().encode('utf-8')
    total_fee = int(HARDCODED_PRICE * 100)
    before_date = DateTime()
    self._simulatePaymentTransaction_getTotalPayablePrice()
    try:
      def mock_absolute_url():
        return "http://example.org"

      def callFakeWechatApi(self, URL, wechat_dict):
        return {"result_code": 'SUCCESS', "code_url": 'weixin://wxpay/bizpayurl?pr=AAAAA' }
      original_method = self.portal.absolute_url
      original_callWechatApi = WechatService.callWechatApi
      self.portal.absolute_url = mock_absolute_url
      WechatService.callWechatApi = callFakeWechatApi
      try:
        event.generateManualPaymentPage()
      finally:
        self.portal.absolute_url = original_method
        WechatService.callWechatApi = original_callWechatApi

    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()

    after_date = DateTime()

    # Payment start date is modified
    self.assertTrue(payment.getStartDate() >= before_date)
    self.assertTrue(payment.getStopDate() <= after_date)

    # Payment is registered
    transaction_date, transaction_id = \
      payment.PaymentTransaction_getWechatId()
    self.assertNotEqual(transaction_date, None)
    self.assertNotEqual(transaction_id, None)

    # Event state
    self.assertEqual(event.getValidationState(), "acknowledged")
    expected_url = "http://example.org/#wechat_payment?trade_no=%s&price=%s&payment_url=" %\
       (payment_transaction_id, total_fee)

    # Event message state
    event_message_list = event.contentValues(portal_type="Wechat Event Message")
    self.assertEqual(len(event_message_list), 1)
    message = event_message_list[0]
    self.assertEqual(message.getTitle(), 'Shown Page')
    self.assertTrue(expected_url in message.getTextContent(), 
      "%s not in %s" % (expected_url, message.getTextContent()))

    transaction.abort()

  def test_updateStatus_noAccountingTransaction(self):
    event = self.createWechatEvent()
    self.assertRaises(AttributeError, event.updateStatus)

  def test_updateStatus_notRegisteredTransaction(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
    )
    self.assertRaises(ValueError, event.updateStatus)

  def test_updateStatus_noPaymentService(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
    )
    _ , _ = payment.PaymentTransaction_generateWechatId()
    self.assertRaises(AttributeError, event.updateStatus)

  def mockQueryWechatOrderStatus(self, method_to_call, expected_args, result_dict):
    payment_service = self.wechat_secure_payment
    def mock_QueryWechatOrderStatus(arg1):
      self.assertEqual(arg1, expected_args)
      return result_dict
    setattr(payment_service, 'queryWechatOrderStatus', mock_QueryWechatOrderStatus)
    try:
      return method_to_call()
    finally:
      del payment_service.queryWechatOrderStatus

  def _simulateWechatEvent_processUpdate(self):
    script_name = 'WechatEvent_processUpdate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by WechatEvent_processUpdate') """ )
    self.commit()

  def _dropWechatEvent_processUpdate(self):
    script_name = 'WechatEvent_processUpdate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_updateStatus_defaultUseCase(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
      source=self.wechat_secure_payment.getRelativeUrl(),
    )
    _, transaction_id = \
      payment.PaymentTransaction_generateWechatId()

    mocked_data_kw = 'mocked_data_kw'

    self._simulateWechatEvent_processUpdate()
    try:
      self.mockQueryWechatOrderStatus(
        event.updateStatus,
        {'out_trade_no': transaction_id},
        mocked_data_kw
      )
    finally:
      self._dropWechatEvent_processUpdate()

    event_message_list = event.contentValues(portal_type="Wechat Event Message")
    self.assertEqual(len(event_message_list), 2)

    sent_message = [x for x in event_message_list \
                    if x.getTitle() == 'Query Order Status'][0]
    self.assertEqual(sent_message.getTextContent(), str({'out_trade_no': transaction_id}))

    received_message = [x for x in event_message_list \
                        if x.getTitle() == 'Received Order Status'][0]
    self.assertEqual(received_message.getPredecessor(), 
                      sent_message.getRelativeUrl())
    self.assertEqual(received_message.getTextContent(), mocked_data_kw)

    self.assertEqual(
        'Visited by WechatEvent_processUpdate',
        event.workflow_history['edit_workflow'][-1]['comment'])

