# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort

import lxml.html
from DateTime import DateTime
from Products.ERP5Type.tests.utils import createZODBPythonScript

HARDCODED_PRICE = -99.6

vads_url_cancel = 'http://example.org/cancel'
vads_url_error = 'http://example.org/error'
vads_url_referral = 'http://example.org/referral'
vads_url_refused = 'http://example.org/refused'
vads_url_success = 'http://example.org/success'
vads_url_return = 'http://example.org/return'

class TestSlapOSPayzenInterfaceWorkflow(SlapOSTestCaseMixinWithAbort):

  def _simulatePaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\nreturn %f' % HARDCODED_PRICE)

  def _dropPaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)

  def test_generateManualPaymentPage_mandatoryParameters(self):
    event = self.createPayzenEvent()
    # vads_url_cancel
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )
    # vads_url_error
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )
    # vads_url_referral
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )
    # vads_url_refused
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )
    # vads_url_success
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_return=vads_url_return,
    )
    # vads_url_return
    self.assertRaises(TypeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
    )

  def test_generateManualPaymentPage_noAccountingTransaction(self):
    event = self.createPayzenEvent()
    self.assertRaises(AttributeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )

  def test_generateManualPaymentPage_registeredTransaction(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    _ , _ = payment.PaymentTransaction_generatePayzenId()
    self.assertRaises(ValueError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )

  def test_generateManualPaymentPage_noPaymentService(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    self.assertRaises(AttributeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )

  def test_generateManualPaymentPage_noCurrency(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
      source="portal_secure_payments/slapos_payzen_test",
    )
    self.assertRaises(AttributeError, event.generateManualPaymentPage,
      vads_url_cancel=vads_url_cancel,
      vads_url_error=vads_url_error,
      vads_url_referral=vads_url_referral,
      vads_url_refused=vads_url_refused,
      vads_url_success=vads_url_success,
      vads_url_return=vads_url_return,
    )

  def test_generateManualPaymentPage_defaultUseCase(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource="currency_module/EUR",
    )
    event.edit(
      destination_value=payment,
      source="portal_secure_payments/slapos_payzen_test",
    )

    before_date = DateTime()
    self._simulatePaymentTransaction_getTotalPayablePrice()
    try:
      event.generateManualPaymentPage(
        vads_url_cancel=vads_url_cancel,
        vads_url_error=vads_url_error,
        vads_url_referral=vads_url_referral,
        vads_url_refused=vads_url_refused,
        vads_url_success=vads_url_success,
        vads_url_return=vads_url_return,
      )
    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()
    after_date = DateTime()

    # Payment start date is modified
    self.assertTrue(payment.getStartDate() >= before_date)
    self.assertTrue(payment.getStopDate() <= after_date)

    # Payment is registered
    transaction_date, transaction_id = \
      payment.PaymentTransaction_getPayzenId()
    self.assertNotEqual(transaction_date, None)
    self.assertNotEqual(transaction_id, None)

    # Event state
    self.assertEqual(event.getValidationState(), "acknowledged")

    data_dict = {
      'vads_language': 'en',
      'vads_url_cancel': vads_url_cancel,
      'vads_url_error': vads_url_error,
      'vads_url_referral': vads_url_referral,
      'vads_url_refused': vads_url_refused,
      'vads_url_success': vads_url_success,
      'vads_url_return': vads_url_return,
      'vads_trans_date': payment.getStartDate().toZone('UTC')\
                           .asdatetime().strftime('%Y%m%d%H%M%S'),
      'vads_amount': str(int(HARDCODED_PRICE * -100)),
      'vads_currency': 978,
      'vads_trans_id': transaction_id,
      'vads_order_id': "%s-%s" % (transaction_date.toZone('UTC')\
                           .asdatetime().strftime('%Y%m%d'), transaction_id),
      'vads_site_id': 'foo',
    }
    # Calculate the signature...
    self.portal.portal_secure_payments.slapos_payzen_test._getFieldList(data_dict)
    data_dict['action'] = 'https://secure.payzen.eu/vads-payment/'

    expected_html_page = lxml.html.tostring(
      lxml.html.fromstring(
'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Script-Type" content="text/javascript" />
<meta http-equiv="Content-Style-Type" content="text/css" />
<title>title</title>
</head>
<body onload="document.payment.submit();">

<form action="%(action)s" id="payment" method="POST" name="payment">

  <input name="signature" type="hidden" value="%(signature)s"></input>


  <input name="vads_action_mode" type="hidden" value="INTERACTIVE"></input>


  <input name="vads_amount" type="hidden" value="%(vads_amount)s"></input>


  <input name="vads_contrib" type="hidden" value="ERP5"></input>


  <input name="vads_ctx_mode" type="hidden" value="TEST"></input>


  <input name="vads_currency" type="hidden" value="%(vads_currency)s"></input>


  <input name="vads_language" type="hidden" value="%(vads_language)s"></input>


  <input name="vads_order_id" type="hidden" value="%(vads_order_id)s"></input>


  <input name="vads_page_action" type="hidden" value="PAYMENT"></input>


  <input name="vads_payment_config" type="hidden" value="SINGLE"></input>


  <input name="vads_site_id" type="hidden" value="%(vads_site_id)s"></input>


  <input name="vads_trans_date" type="hidden" value="%(vads_trans_date)s"></input>


  <input name="vads_trans_id" type="hidden" value="%(vads_trans_id)s"></input>


  <input name="vads_url_cancel" type="hidden" value="%(vads_url_cancel)s"></input>


  <input name="vads_url_error" type="hidden" value="%(vads_url_error)s"></input>


  <input name="vads_url_referral" type="hidden" value="%(vads_url_referral)s"></input>


  <input name="vads_url_refused" type="hidden" value="%(vads_url_refused)s"></input>


  <input name="vads_url_return" type="hidden" value="%(vads_url_return)s"></input>


  <input name="vads_url_success" type="hidden" value="%(vads_url_success)s"></input>


  <input name="vads_version" type="hidden" value="V2"></input>


<center>
  <input type="submit" value="Click to pay"></input>
</center>
</form>
</body>
</html>''' % data_dict), method='c14n')

    # Event message state
    event_message_list = event.contentValues(portal_type="Payzen Event Message")
    self.assertEqual(len(event_message_list), 1)
    message = event_message_list[0]
    self.assertEqual(message.getTitle(), 'Shown Page')

    message_text_content = lxml.html.tostring(
      lxml.html.fromstring(message.getTextContent()), method='c14n')
    self.assertEqual(message_text_content, expected_html_page)

  def test_updateStatus_noAccountingTransaction(self):
    event = self.createPayzenEvent()
    self.assertRaises(AttributeError, event.updateStatus)

  def test_updateStatus_notRegisteredTransaction(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
    )
    self.assertRaises(ValueError, event.updateStatus)

  def test_updateStatus_noPaymentService(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
    )
    _ , _ = payment.PaymentTransaction_generatePayzenId()
    self.assertRaises(AttributeError, event.updateStatus)

  def mockRestGetInfo(self, method_to_call, expected_args, result_tuple):
    payment_service = self.portal.portal_secure_payments.slapos_payzen_test
    def mockrest_getInfo(arg1, arg2):
      self.assertEqual(arg1, expected_args[0])
      self.assertEqual(arg2, expected_args[1])
      return result_tuple
    setattr(payment_service, 'rest_getInfo', mockrest_getInfo)
    try:
      return method_to_call()
    finally:
      del payment_service.rest_getInfo

  def _simulatePayzenEvent_processUpdate(self):
    script_name = 'PayzenEvent_processUpdate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PayzenEvent_processUpdate') """ )
    self.commit()

  def _dropPayzenEvent_processUpdate(self):
    script_name = 'PayzenEvent_processUpdate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_updateStatus_defaultUseCase(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(
      destination_value=payment,
      source="portal_secure_payments/slapos_payzen_test",
    )
    transaction_date, transaction_id = \
      payment.PaymentTransaction_generatePayzenId()

    mocked_data_kw = 'mocked_data_kw'
    mocked_sent_text = 'mocked_sent_text'
    mocked_received_text = 'mocked_received_text'

    self._simulatePayzenEvent_processUpdate()
    try:
      self.mockRestGetInfo(
        event.updateStatus,
        (transaction_date.toZone('UTC').asdatetime(),
          "%s-%s" % (transaction_date.toZone('UTC')\
                           .asdatetime().strftime('%Y%m%d'), transaction_id)),
        (mocked_data_kw, mocked_sent_text, mocked_received_text),
      )
    finally:
      self._dropPayzenEvent_processUpdate()

    event_message_list = event.contentValues(portal_type="Payzen Event Message")
    self.assertEqual(len(event_message_list), 2)

    sent_message = [x for x in event_message_list \
                    if x.getTitle() == 'Sent Data'][0]
    self.assertEqual(sent_message.getTextContent(), mocked_sent_text)

    received_message = [x for x in event_message_list \
                        if x.getTitle() == 'Received Data'][0]
    self.assertEqual(received_message.getPredecessor(), 
                      sent_message.getRelativeUrl())
    self.assertEqual(received_message.getTextContent(), mocked_received_text)

    self.assertEqual(
        'Visited by PayzenEvent_processUpdate',
        event.workflow_history['edit_workflow'][-1]['comment'])

