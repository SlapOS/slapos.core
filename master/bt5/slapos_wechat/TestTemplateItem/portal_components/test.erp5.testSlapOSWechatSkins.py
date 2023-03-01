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
    self.assertEqual(mapping, payment_transaction.getId())
    self.assertTrue(mapping.startswith(
      '%s.' % transaction_date.asdatetime().strftime('%Y%m%d')
    ))
    self.assertTrue(mapping.endswith(
      '-%s' % wechat_id.split('-')[1]
    ))
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
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("PSERV-Wechat-Test")
    payment_transaction = self.createPaymentTransaction()
    wechat_event = payment_transaction.PaymentTransaction_createWechatEvent()
    self.assertEqual(wechat_event.getPortalType(), "Wechat Event")
    self.assertEqual(wechat_event.getSource(),
      "portal_secure_payments/slapos_wechat_test")
    self.assertEqual(wechat_event.getDestination(), payment_transaction.getRelativeUrl())

  def test_createWechatEvent_kwParameter(self):
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("PSERV-Wechat-Test")
    self.tic()
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
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("PSERV-Wechat-Test")
    self.tic()
    result = self.portal.Base_getWechatServiceRelativeUrl()
    self.assertEqual(result, 'portal_secure_payments/slapos_wechat_test')

  def test_getWechatServiceRelativeUrl_not_found(self):
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("disabled")
    self.tic()
    result = self.portal.Base_getWechatServiceRelativeUrl()
    self.assertEqual(result, None)


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
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("PSERV-Wechat-Test")
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      payment_mode="wechat",
      destination_section_value=person,
      destination_project_value=project
    )
    self.tic()
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      destination_project_value=project,
      resource_value=self.portal.currency_module.CNY,
      ledger="automated",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')
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
    self.portal.portal_secure_payments.slapos_wechat_test.setReference("PSERV-Wechat-Test")
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      payment_mode="wechat",
      destination_section_value=person,
      destination_project_value=project
    )
    self.tic()
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      destination_project_value=project,
      resource_value=self.portal.currency_module.CNY,
      ledger="automated",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')
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
    project = self.addProject()
    person = self.makePerson(project)
    invoice =  self.createStoppedSaleInvoiceTransaction(
      payment_mode="wechat",
      destination_section_value=person,
      destination_project_value=project
    )
    self.tic()
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='wechat',
      causality_value=invoice,
      destination_section=invoice.getDestinationSection(),
      destination_project_value=project,
      resource_value=self.portal.currency_module.CNY,
      ledger="automated",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

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

    system_event_list = payment.getDestinationRelatedValueList(portal_type="Payzen Event")
    self.assertEqual(len(system_event_list), 0)