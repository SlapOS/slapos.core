# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
from erp5.component.document.WechatService import WechatService


from DateTime import DateTime
from zExceptions import Unauthorized
import transaction
from Products.ERP5Type.tests.utils import createZODBPythonScript

class TestSlapOSCurrency_getIntegrationMapping(SlapOSTestCaseMixinWithAbort):

  def test_integratedCurrency(self):
    currency = self.portal.currency_module.CNY
    self.assertEqual(currency.Currency_getIntegrationMapping(), 'CNY')

  def test_getIntegrationMapping_notIntegratedCurrency(self):
    new_id = self.generateNewId()
    currency = self.portal.currency_module.newContent(
      portal_type='Currency',
      title="Currency %s" % new_id,
      reference="TESTCUR-%s" % new_id,
      )
    self.assertRaises(
      AssertionError,
      currency.Currency_getIntegrationMapping)


class TestSlapOSAccountingTransaction_updateStartDate(SlapOSTestCaseMixinWithAbort):

  def test_date_changed(self):
    date = DateTime("2001/01/01")
    payment_transaction = self.createPaymentTransaction()
    payment_transaction.AccountingTransaction_updateStartDate(date)
    self.assertEqual(payment_transaction.getStartDate(), date)

  def test_REQUEST_disallowed(self):
    date = DateTime()
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.AccountingTransaction_updateStartDate,
      date, REQUEST={})


class TestSlapOSPaymentTransaction_getWechatId(SlapOSTestCaseMixinWithAbort):

  def test_getWechatId_newPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertEqual(payment_transaction.PaymentTransaction_getWechatId(), (None, None))

  def test_getWechatId_mappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    transaction_date, wechat_id = payment_transaction.PaymentTransaction_generateWechatId()
    transaction_date2, wechat_id2 = payment_transaction.PaymentTransaction_getWechatId()
    self.assertEqual(wechat_id, wechat_id2)
    self.assertEqual(transaction_date, transaction_date2)

  def test_getWechatId_manualMappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    integration_site = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredWechatIntegrationSite())

    try:
      integration_site.getCategoryFromMapping(
        'Causality/%s' % payment_transaction.getId().replace('-', '_'),
      create_mapping_line=True,
      create_mapping=True)
    except ValueError:
      pass
    integration_site.Causality[payment_transaction.getId().replace('-', '_')].\
      setDestinationReference("20010101-123456")

    transaction_date, wechat_id = payment_transaction.PaymentTransaction_getWechatId()
    self.assertEqual(wechat_id, "20010101-123456")
    self.assertEqual(transaction_date, DateTime("20010101"))

  def test_getWechatId_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_getWechatId,
      REQUEST={})


class TestSlapOSPaymentTransaction_generateWechatId(SlapOSTestCaseMixinWithAbort):

  def test_generateWechatId_newPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    transaction_url = payment_transaction.getId().replace('-', '_')

    integration_site = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredWechatIntegrationSite())

    # Integration tool returns category value as mapping if nothing is set
    mapping = integration_site.getCategoryFromMapping(
      'Causality/%s' % transaction_url)
    self.assertEqual(mapping, 'causality/%s' % transaction_url)
    category = integration_site.getMappingFromCategory(mapping)
    self.assertEqual(category, 'Causality/%s' % transaction_url)

    transaction_date, wechat_id = payment_transaction.PaymentTransaction_generateWechatId()

    mapping = integration_site.getCategoryFromMapping(
      'Causality/%s' % transaction_url)
    self.assertEqual(mapping, "%s-%s" % (
      transaction_date.asdatetime().strftime('%Y%m%d'), wechat_id.split('-')[1]))
    category = integration_site.getMappingFromCategory('causality/%s' % mapping)
    # XXX Not indexed yet
#     self.assertEqual(category, 'Causality/%s' % transaction_url)

    self.assertNotEqual(wechat_id, None)

    self.assertNotEqual(transaction_date, None)
    self.assertEqual(transaction_date.timezone(), 'UTC')
    self.assertEqual(transaction_date.asdatetime().strftime('%Y%m%d'),
                      DateTime().toZone('UTC').asdatetime().strftime('%Y%m%d'))


  def test_generateWechatId_mappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    payment_transaction.PaymentTransaction_generateWechatId()
    wechat_id = payment_transaction.PaymentTransaction_generateWechatId()
    self.assertEqual(wechat_id, (None, None))

  def test_generateWechatId_differentPaymentId(self):
    payment_transaction = self.createPaymentTransaction()
    payment_transaction2 = self.createPaymentTransaction()
    date, wechat_id = payment_transaction.PaymentTransaction_generateWechatId()
    date2, wechat_id2 = payment_transaction2.PaymentTransaction_generateWechatId()
    self.assertEqual(date.asdatetime().strftime('%Y%m%d'),
                      date2.asdatetime().strftime('%Y%m%d'))
    self.assertNotEqual(wechat_id, wechat_id2)

  def test_generateWechatId_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_generateWechatId,
      REQUEST={})


class TestSlapOSPaymentTransaction_createWechatEvent(SlapOSTestCaseMixinWithAbort):

  def test_createWechatEvent_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_createWechatEvent,
      REQUEST={})

  def test_createWechatEvent_newPayment(self):
    payment_transaction = self.createPaymentTransaction()
    wechat_event = payment_transaction.PaymentTransaction_createWechatEvent()
    self.assertEqual(wechat_event.getPortalType(), "Wechat Event")
    self.assertEqual(wechat_event.getSource(),
      "portal_secure_payments/slapos_wechat_test")
    self.assertEqual(wechat_event.getDestination(), payment_transaction.getRelativeUrl())

  def test_createWechatEvent_kwParameter(self):
    payment_transaction = self.createPaymentTransaction()
    wechat_event = payment_transaction.PaymentTransaction_createWechatEvent(
      title='foo')
    self.assertEqual(wechat_event.getPortalType(), "Wechat Event")
    self.assertEqual(wechat_event.getSource(),
      "portal_secure_payments/slapos_wechat_test")
    self.assertEqual(wechat_event.getDestination(), payment_transaction.getRelativeUrl())
    self.assertEqual(wechat_event.getTitle(), "foo")


class TestSlapOSWechatEvent_processUpdate(SlapOSTestCaseMixinWithAbort):

  def test_processUpdate_REQUEST_disallowed(self):
    event = self.createWechatEvent()
    self.assertRaises(
      Unauthorized,
      event.WechatEvent_processUpdate,
      '',
      REQUEST={})

  def test_processUpdate_noTransaction(self):
    event = self.createWechatEvent()
    self.assertRaises(
      AttributeError,
      event.WechatEvent_processUpdate,
      'a')

  def test_processUpdate_wrongDataDictionnary(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    self.assertRaises(
      TypeError,
      event.WechatEvent_processUpdate,
      'a')

  def test_processUpdate_unknownErrorCode(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'FOO',
    }

    event.WechatEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Unknown Wechat result_code 'FOO'",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_unknownTransactionStatus(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'FOO',
    }

    event.WechatEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Unknown transactionStatus 'FOO'",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_notSupportedTransactionStatus(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'REVOKED',
    }

    event.WechatEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Transaction status 'REVOKED' ('Order revoked') " \
        "is not supported",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_notProcessedTransactionStatus(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'USERPAYING',
    }

    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Automatic acknowledge as result of correct communication',
        event.workflow_history['system_event_workflow'][-1]['comment'])

    self.assertEqual(payment.getSimulationState(), "confirmed")
    self.assertEqual(
        'Transaction status USERPAYING (Awaiting user to pay) did not changed ' \
        'the document state',
        payment.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(
        'Confirmed as really saw in WeChat.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

  def test_processUpdate_notProcessedTransactionStatusConfirmedPayment(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    payment.confirm()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'USERPAYING',
    }
    event.WechatEvent_processUpdate(data_kw)

  def test_processUpdate_noAuthAmount(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
    }

    self.assertRaises(
      KeyError,
      event.WechatEvent_processUpdate,
      data_kw)

  def test_processUpdate_noAuthDevise(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
      'total_fee': 1,
    }

    self.assertRaises(
      KeyError,
      event.WechatEvent_processUpdate,
      data_kw)

  def test_processUpdate_differentAmount(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
      'total_fee': 1,
      'fee_type': 'CNY',
    }

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        'Received amount (1) does not match stored on transaction (0)',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_differentDevise(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/CNY',
      start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
      'total_fee': 0,
      'fee_type': 'EUR',
    }

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Received devise ('EUR') does not match stored on transaction ('CNY')",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_cancelledTransaction(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/CNY',
      start_date=DateTime())
    payment.cancel()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
      'total_fee': 0,
      'fee_type': 'CNY',
    }

    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        'Expected to put transaction in stopped state, but achieved only ' \
        'cancelled state',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_defaultUseCase(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/CNY',
      start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'SUCCESS',
      'total_fee': 0,
      'fee_type': 'CNY',
    }

    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(payment.getSimulationState(), "stopped")
    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Automatic acknowledge as result of correct communication',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def _simulatePaymentTransaction_getRecentWechatId(self):
    script_name = 'PaymentTransaction_getWechatId'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""return DateTime().toZone('UTC'), 'foo'""")

  def _simulatePaymentTransaction_getOldWechatId(self):
    script_name = 'PaymentTransaction_getWechatId'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""from erp5.component.module.DateUtils import addToDate
return addToDate(DateTime(), to_add={'day': -1, 'second': -1}).toZone('UTC'), 'foo'""")

  def _dropPaymentTransaction_getWechatId(self):
    script_name = 'PaymentTransaction_getWechatId'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)

  def test_processUpdate_recentNotFoundOnWechatSide(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'FAIL',
      'err_code': 'INVALID_TRANSACTIONID',
    }

    self._simulatePaymentTransaction_getRecentWechatId()
    try:
      event.WechatEvent_processUpdate(data_kw)
    finally:
      self._dropPaymentTransaction_getWechatId()

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Error when getting transaction status: INVALID_TRANSACTIONID',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertNotEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Error code FAIL did not changed the document state.',
        payment.workflow_history['edit_workflow'][-1]['comment'])

  def test_processUpdate_oldNotFoundOnWechatSide(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'FAIL',
      'err_code': 'INVALID_TRANSACTIONID',
    }

    self._simulatePaymentTransaction_getOldWechatId()
    try:
      event.WechatEvent_processUpdate(data_kw)
    finally:
      self._dropPaymentTransaction_getWechatId()

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Error when getting transaction status: INVALID_TRANSACTIONID',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Aborting failing wechat payment.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

  def test_processUpdate_refusedWechatPayment(self):
    event = self.createWechatEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'result_code': 'SUCCESS',
      'trade_state': 'CLOSED',
    }

    event.WechatEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Refused wechat payment.',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Aborting refused wechat payment.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

class TestSlapOSWechatBase_getWechatServiceRelativeUrl(SlapOSTestCaseMixinWithAbort):

  def test_getWechatServiceRelativeUrl_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Base_getWechatServiceRelativeUrl,
      REQUEST={})

  def test_getWechatServiceRelativeUrl_default_result(self):
    result = self.portal.Base_getWechatServiceRelativeUrl()
    self.assertEqual(result, 'portal_secure_payments/slapos_wechat_test')

class TestSlapOSWechatAccountingTransaction_getPaymentState(
                                                    SlapOSTestCaseMixinWithAbort):

  def test_AccountingTransaction_getPaymentState_draft_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_deleted_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.delete()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_cancelled_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.cancel()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_planned_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.plan()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_confirmed_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.setStartDate(DateTime())
    invoice.confirm()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_started_payment(self):
    invoice = self.createSaleInvoiceTransaction()
    invoice.start()
    self.assertEqual("Ongoing", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_reversed_payment(self):
    invoice =  self.createWechatSaleInvoiceTransaction()
    self.tic()
    reversal = invoice.SaleInvoiceTransaction_createReversalWechatTransaction()
    self.tic()
    self.assertEqual("Cancelled", invoice.AccountingTransaction_getPaymentState())
    self.assertEqual(0, invoice.getTotalPrice() + reversal.getTotalPrice())

  def test_AccountingTransaction_getPaymentState_free_payment(self):
    invoice =  self.createWechatSaleInvoiceTransaction(price=0)
    self.tic()
    self.assertEqual("Free!", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_unpaid_payment(self):
    invoice =  self.createWechatSaleInvoiceTransaction()
    # If payment is not indexed or not started the state should be unpaid
    self.assertEqual("Unpaid", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_paynow_payment(self):
    person = self.makePerson()
    invoice =  self.createWechatSaleInvoiceTransaction(
      destination_section=person.getRelativeUrl())
    self.tic()
    self.login(person.getUserId())
    self.assertEqual("Pay Now", invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_waiting_payment(self):
    person = self.makePerson()
    invoice =  self.createWechatSaleInvoiceTransaction(
      destination_section=person.getRelativeUrl())
    self.tic()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    payment.PaymentTransaction_generateWechatId()
    self.login(person.getUserId())
    self.assertEqual("Waiting for payment confirmation",
                      invoice.AccountingTransaction_getPaymentState())

  def test_AccountingTransaction_getPaymentState_paid_payment(self):
    invoice =  self.createWechatSaleInvoiceTransaction()
    self.tic()
    for line in invoice.getMovementList(self.portal.getPortalAccountingMovementTypeList()):
      node_value = line.getSourceValue(portal_type='Account')
      if node_value.getAccountType() == 'asset/receivable':
        line.setGroupingReference("TEST%s" % self.new_id)
    self.assertEqual("Paid", invoice.AccountingTransaction_getPaymentState())

class TestSlapOSWechatPaymentTransaction_redirectToManualWechatPayment(
                                                    SlapOSTestCaseMixinWithAbort):


  def test_PaymentTransaction_redirectToManualWechatPayment(self):
    payment = self.createPaymentTransaction()
    self.assertRaises(ValueError, payment.PaymentTransaction_redirectToManualWechatPayment)

  def _simulatePaymentTransaction_getVADSUrlDict(self):
    script_name = 'PaymentTransaction_getVADSUrlDict'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""payment_transaction_url = context.getRelativeUrl()
return dict(vads_url_already_registered="%s/already_registered" % (payment_transaction_url),
  vads_url_cancel="%s/cancel" % (payment_transaction_url),
  vads_url_error="%s/error" % (payment_transaction_url),
  vads_url_referral="%s/referral" % (payment_transaction_url),
  vads_url_refused="%s/refused" % (payment_transaction_url),
  vads_url_success="%s/success" % (payment_transaction_url),
  vads_url_return="%s/return" % (payment_transaction_url),
)""")

  def _dropPaymentTransaction_getVADSUrlDict(self):
    script_name = 'PaymentTransaction_getVADSUrlDict'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)


  def test_PaymentTransaction_redirectToManualWechatPayment_unauthorzied(self):
    payment = self.createPaymentTransaction()
    self._simulatePaymentTransaction_getVADSUrlDict()
    self.logout()
    try:
      self.assertRaises(Unauthorized, payment.PaymentTransaction_redirectToManualWechatPayment)
    finally:
      self.login()
      self._dropPaymentTransaction_getVADSUrlDict()

  def test_PaymentTransaction_redirectToManualWechatPayment_redirect(self):
    person = self.makePerson()
    invoice =  self.createWechatSaleInvoiceTransaction(
      destination_section=person.getRelativeUrl())
    self.tic()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    payment.setResourceValue(self.portal.currency_module.EUR)
    payment_transaction_id = payment.getId()

    self.tic()
    self.login(person.getUserId())
    self._simulatePaymentTransaction_getVADSUrlDict()
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
        redirected_url = payment.PaymentTransaction_redirectToManualWechatPayment()
      finally:
        self.portal.absolute_url = original_method
        WechatService.callWechatApi = original_callWechatApi
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    expected = "http://example.org/#wechat_payment?trade_no=%s&price=0&payment_url=weixin://wxpay/bizpayurl?pr=" % payment_transaction_id
    self.assertTrue(redirected_url.startswith(expected),
        "%s do not start with %s" % (redirected_url, expected))
    transaction.abort()

  def test_PaymentTransaction_redirectToManualWechatPayment_redirect_with_website(self):
    person = self.makePerson()
    invoice =  self.createWechatSaleInvoiceTransaction(
      destination_section=person.getRelativeUrl())
    self.tic()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    payment.setResourceValue(self.portal.currency_module.EUR)
    payment_transaction_id = payment.getId()
    web_site = self.portal.web_site_module.newContent(portal_type='Web Site')

    self.tic()
    self.login(person.getUserId())
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      def callFakeWechatApi(self, URL, wechat_dict):
        return {"result_code": 'SUCCESS', "code_url": 'weixin://wxpay/bizpayurl?pr=AAAAA' }
      original_callWechatApi = WechatService.callWechatApi
      WechatService.callWechatApi = callFakeWechatApi
      try:
        redirected_url = payment.PaymentTransaction_redirectToManualWechatPayment(web_site)
      finally:
        WechatService.callWechatApi = original_callWechatApi
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    expected = "%s/wechat_payment?trade_no=%s&price=0&payment_url=weixin://wxpay/bizpayurl?pr=" % (web_site.absolute_url(), payment_transaction_id)
    self.assertTrue(redirected_url.startswith(expected),
        "%s do not start with %s" % (redirected_url, expected))
    transaction.abort()


  def test_PaymentTransaction_redirectToManualWechatPayment_already_registered(self):
    person = self.makePerson()
    invoice =  self.createWechatSaleInvoiceTransaction(
      destination_section=person.getRelativeUrl())
    self.tic()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    payment.setResourceValue(self.portal.currency_module.EUR)
    payment.PaymentTransaction_generateWechatId()
    self.tic()
    self.login(person.getUserId())
    self._simulatePaymentTransaction_getVADSUrlDict()
    try:
      redirect = payment.PaymentTransaction_redirectToManualWechatPayment()
    finally:
      self._dropPaymentTransaction_getVADSUrlDict()

    self.assertEqual("%s/already_registered" % payment.getRelativeUrl(),
                      redirect)

class TestSlapOSWechatSaleInvoiceTransaction_getWechatPaymentRelatedValue(
                                                    SlapOSTestCaseMixinWithAbort):

  def test_SaleInvoiceTransaction_getWechatPaymentRelatedValue(self):
    invoice =  self.createWechatSaleInvoiceTransaction()
    self.tic()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    self.assertNotEqual(None, payment)
    self.assertEqual(payment.getSimulationState(), "started")
    self.assertEqual(payment.getCausalityValue(), invoice)
    self.assertEqual(payment.getPaymentModeUid(),
      self.portal.portal_categories.payment_mode.wechat.getUid())

    payment.setStartDate(DateTime())
    payment.stop()
    payment.immediateReindexObject()
    payment = invoice.SaleInvoiceTransaction_getWechatPaymentRelatedValue()
    self.assertEqual(None, payment)

class TestSlapOSWechatSaleInvoiceTransaction_createReversalWechatTransaction(
                                                    SlapOSTestCaseMixinWithAbort):

  def test_createReversalWechatTransaction_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SaleInvoiceTransaction_createReversalWechatTransaction,
      REQUEST={})

  def test_createReversalWechatTransaction_bad_portal_type(self):
    self.assertRaises(
      AssertionError,
      self.portal.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_bad_payment_mode(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    invoice.edit(payment_mode="cash")
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_bad_state(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    self.portal.portal_workflow._jumpToStateFor(invoice, 'delivered')
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_zero_price(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    invoice.manage_delObjects(invoice.contentIds())
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_wrong_trade_condition(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    invoice.edit(specialise=None)
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_paid(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    line = invoice.contentValues(portal_type="Sale Invoice Transaction Line")[0]
    line.edit(grouping_reference="azerty")
    self.tic()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_no_payment(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    # Do not reindex payment. portal_catalog will not find it.
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_no_wechat_payment(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    self.tic()
    payment = invoice.getCausalityRelatedValue()
    payment.edit(payment_mode="cash")
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_no_payment_state(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    self.tic()
    payment = invoice.getCausalityRelatedValue()
    self.portal.portal_workflow._jumpToStateFor(payment, 'cancelled')
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_registered_payment(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    self.tic()
    payment = invoice.getCausalityRelatedValue()
    payment.PaymentTransaction_generateWechatId()
    self.assertRaises(
      AssertionError,
      invoice.SaleInvoiceTransaction_createReversalWechatTransaction)

  def test_createReversalWechatTransaction_ok(self):
    invoice = self.createWechatSaleInvoiceTransaction()
    self.tic()
    payment = invoice.getCausalityRelatedValue()
    reversale_invoice = invoice.\
      SaleInvoiceTransaction_createReversalWechatTransaction()

    self.assertEqual(invoice.getPaymentMode(""), "")
    self.assertEqual(payment.getPaymentMode(""), "")
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(reversale_invoice.getTitle(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getDescription(),
                     "Reversal Transaction for %s" % invoice.getTitle())
    self.assertEqual(reversale_invoice.getCausality(),
                     invoice.getRelativeUrl())
    self.assertEqual(reversale_invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getSimulationState(), "stopped")

    invoice_line_id = invoice.contentValues(portal_type="Invoice Line")[0].getId()
    transaction_line_id = invoice.contentValues(
      portal_type="Sale Invoice Transaction Line")[0].getId()

    self.assertEqual(invoice[invoice_line_id].getQuantity(),
                     -reversale_invoice[invoice_line_id].getQuantity())
    self.assertEqual(reversale_invoice[invoice_line_id].getQuantity(), 2)

    self.assertEqual(invoice[transaction_line_id].getQuantity(),
                     -reversale_invoice[transaction_line_id].getQuantity())
    self.assertEqual(reversale_invoice[transaction_line_id].getQuantity(), 3)
    self.assertEqual(len(invoice.getMovementList()), 2)

    # Both invoice should have a grouping reference
    self.assertNotEqual(invoice[transaction_line_id].getGroupingReference(""),
                        "")
    self.assertEqual(
      invoice[transaction_line_id].getGroupingReference("1"),
      reversale_invoice[transaction_line_id].getGroupingReference("2"))

    # All references should be regenerated
    self.assertNotEqual(invoice.getReference(""),
                        reversale_invoice.getReference(""))
    self.assertNotEqual(invoice.getSourceReference(""),
                        reversale_invoice.getSourceReference(""))
    self.assertNotEqual(invoice.getDestinationReference(""),
                        reversale_invoice.getDestinationReference(""))

    # Another trade condition
    self.assertEqual(
      reversale_invoice.getSpecialise(),
      "sale_trade_condition_module/slapos_manual_accounting_trade_condition")
    self.tic()

