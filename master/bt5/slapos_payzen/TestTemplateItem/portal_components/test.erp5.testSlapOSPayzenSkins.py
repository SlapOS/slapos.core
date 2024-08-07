# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort, \
  SlapOSTestCaseMixin, simulate

from DateTime import DateTime
from zExceptions import Unauthorized

class TestSlapOSPayzenMixin(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.payzen_secure_payment = self.portal.portal_secure_payments.newContent(
      portal_type="Payzen Service",
      reference="PSERV-Payzen-Test-%s" % self.generateNewId()
    )

    # Include a simple Integration site
    self.integration_site = self.portal.portal_integrations.newContent(
      title="Integration site for: %s" % (self.payzen_secure_payment),
      reference="payzen",
      portal_type="Integration Site"
    )
    self.integration_site.newContent(
      id="Causality",
      portal_type="Integration Base Category Mapping",
      default_source_reference="Causality",
      default_destination_reference="causality"
    )

    resource_map = self.integration_site.newContent(
      id="Resource",
      portal_type="Integration Base Category Mapping",
      default_source_reference="Resource",
      default_destination_reference="resource"
    )
    resource_map.newContent(
      # This is required for integration
      id='978',
      portal_type="Integration Category Mapping",
      default_destination_reference='resource/currency_module/EUR',
      default_source_reference='978'
    )

    system_preference = self.portal.portal_preferences.slapos_default_system_preference
    self.older_service_reference = system_preference.getPreferredPayzenPaymentServiceReference()
    system_preference.setPreferredPayzenPaymentServiceReference(
      self.payzen_secure_payment.getReference())

    self.older_integration_site = system_preference.getPreferredPayzenIntegrationSite()
    system_preference.setPreferredPayzenIntegrationSite(
      self.integration_site.getRelativeUrl()
    )

    self.tic()

  def beforeTearDown(self):
    SlapOSTestCaseMixin.beforeTearDown(self)
    self.portal.portal_secure_payments.manage_delObjects(
      ids=[self.payzen_secure_payment.getId()])
    self.portal.portal_integrations.manage_delObjects(
      ids=[self.integration_site.getId()])

    system_preference = self.portal.portal_preferences.slapos_default_system_preference
    system_preference.setPreferredPayzenPaymentServiceReference(
      self.older_service_reference)
    system_preference.setPreferredPayzenIntegrationSite(
      self.older_integration_site
    )
    
    self.tic()


class TestSlapOSCurrency_getIntegrationMapping(TestSlapOSPayzenMixin):

  def test_integratedCurrency(self):
    currency = self.portal.currency_module.EUR
    self.assertEqual(currency.Currency_getIntegrationMapping(), '978')

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


class TestSlapOSPaymentTransaction_getPayzenId(TestSlapOSPayzenMixin):

  def test_getPayzenId_newPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertEqual(payment_transaction.PaymentTransaction_getPayzenId(), (None, None))

  def test_getPayzenId_mappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    transaction_date, payzen_id = payment_transaction.PaymentTransaction_generatePayzenId()
    transaction_date2, payzen_id2 = payment_transaction.PaymentTransaction_getPayzenId()
    self.assertEqual(payzen_id, payzen_id2)
    self.assertEqual(transaction_date, transaction_date2)

  def test_getPayzenId_manualMappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    integration_site = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredPayzenIntegrationSite())

    try:
      integration_site.getCategoryFromMapping(
        'Causality/%s' % payment_transaction.getId().replace('-', '_'),
      create_mapping_line=True,
      create_mapping=True)
    except ValueError:
      pass
    integration_site.Causality[payment_transaction.getId().replace('-', '_')].\
      setDestinationReference("20010101_123456")

    transaction_date, payzen_id = payment_transaction.PaymentTransaction_getPayzenId()
    self.assertEqual(payzen_id, "123456")
    self.assertEqual(transaction_date, DateTime("20010101"))

  def test_getPayzenId_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_getPayzenId,
      REQUEST={})


class TestSlapOSPaymentTransaction_generatePayzenId(TestSlapOSPayzenMixin):

  def test_generatePayzenId_newPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    transaction_url = payment_transaction.getId().replace('-', '_')

    integration_site = self.portal.restrictedTraverse(
      self.portal.portal_preferences.getPreferredPayzenIntegrationSite())

    # Integration tool returns category value as mapping if nothing is set
    mapping = integration_site.getCategoryFromMapping(
      'Causality/%s' % transaction_url)
    self.assertEqual(mapping, 'causality/%s' % transaction_url)
    category = integration_site.getMappingFromCategory(mapping)
    self.assertEqual(category, 'Causality/%s' % transaction_url)

    transaction_date, payzen_id = payment_transaction.PaymentTransaction_generatePayzenId()

    mapping = integration_site.getCategoryFromMapping(
      'Causality/%s' % transaction_url)
    self.assertEqual(mapping, "%s_%s" % (
      transaction_date.asdatetime().strftime('%Y%m%d'), payzen_id))
    category = integration_site.getMappingFromCategory('causality/%s' % mapping)
    # XXX Not indexed yet
#     self.assertEqual(category, 'Causality/%s' % transaction_url)

    self.assertNotEqual(payzen_id, None)
    self.assertEqual(len(payzen_id), 6)
    self.assertEqual(str(int(payzen_id)).zfill(6), payzen_id)

    self.assertNotEqual(transaction_date, None)
    self.assertEqual(transaction_date.timezone(), 'UTC')
    self.assertEqual(transaction_date.asdatetime().strftime('%Y%m%d'),
                      DateTime().toZone('UTC').asdatetime().strftime('%Y%m%d'))


  def test_generatePayzenId_mappedPaymentTransaction(self):
    payment_transaction = self.createPaymentTransaction()
    payment_transaction.PaymentTransaction_generatePayzenId()
    payzen_id = payment_transaction.PaymentTransaction_generatePayzenId()
    self.assertEqual(payzen_id, (None, None))

  def test_generatePayzenId_increasePaymentId(self):
    payment_transaction = self.createPaymentTransaction()
    payment_transaction2 = self.createPaymentTransaction()
    date, payzen_id = payment_transaction.PaymentTransaction_generatePayzenId()
    date2, payzen_id2 = payment_transaction2.PaymentTransaction_generatePayzenId()
    self.assertEqual(date.asdatetime().strftime('%Y%m%d'),
                      date2.asdatetime().strftime('%Y%m%d'))
    self.assertNotEqual(payzen_id, payzen_id2)
    self.assertTrue(int(payzen_id) < int(payzen_id2))

  def test_generatePayzenId_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_generatePayzenId,
      REQUEST={})


class TestSlapOSPaymentTransaction_createPayzenEvent(TestSlapOSPayzenMixin):

  def test_createPayzenEvent_REQUEST_disallowed(self):
    payment_transaction = self.createPaymentTransaction()
    self.assertRaises(
      Unauthorized,
      payment_transaction.PaymentTransaction_createPayzenEvent,
      REQUEST={})

  def test_createPayzenEvent_newPayment(self):
    payment_transaction = self.createPaymentTransaction()
    payzen_event = payment_transaction.PaymentTransaction_createPayzenEvent()
    self.assertEqual(payzen_event.getPortalType(), "Payzen Event")
    self.assertEqual(payzen_event.getSource(),
      self.payzen_secure_payment.getRelativeUrl())
    self.assertEqual(payzen_event.getDestination(),
      payment_transaction.getRelativeUrl())

  def test_createPayzenEvent_kwParameter(self):
    payment_transaction = self.createPaymentTransaction()
    payzen_event = payment_transaction.PaymentTransaction_createPayzenEvent(
      title='foo')
    self.assertEqual(payzen_event.getPortalType(), "Payzen Event")
    self.assertEqual(payzen_event.getSource(),
      self.payzen_secure_payment.getRelativeUrl())
    self.assertEqual(payzen_event.getDestination(), payment_transaction.getRelativeUrl())
    self.assertEqual(payzen_event.getTitle(), "foo")


class TestSlapOSPayzenEvent_processUpdate(SlapOSTestCaseMixinWithAbort):

  def test_processUpdate_REQUEST_disallowed(self):
    event = self.createPayzenEvent()
    self.assertRaises(
      Unauthorized,
      event.PayzenEvent_processUpdate,
      'a',
      REQUEST={})

  def test_processUpdate_noTransaction(self):
    event = self.createPayzenEvent()
    self.assertRaises(
      ValueError,
      event.PayzenEvent_processUpdate,
      'a')

  def test_processUpdate_wrongDataDictionnary(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)
    self.assertRaises(
      TypeError,
      event.PayzenEvent_processUpdate,
      'a')

  def test_processUpdate_unknownErrorCode(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      'status': 'ERROR',
      'answer': {
          'errorCode': "foo",
      },
    }

    event.PayzenEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Unknown errorCode 'foo', message: ",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_noTransactionsForOrder(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Unexpected Number of Transaction for this order",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_tooManyTransactionsForOrder(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "ACCEPTED",
          },
          {
            "detailedStatus": "ACCEPTED",
          },
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Unexpected Number of Transaction for this order",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_notSupportedTransactionStatus(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "ACCEPTED",
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)
    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Transaction status 'ACCEPTED' " \
        "is not supported",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_notProcessedTransactionStatus(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "WAITING_AUTHORISATION_TO_VALIDATE",
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw, None)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Automatic acknowledge as result of correct communication',
        event.workflow_history['system_event_workflow'][-1]['comment'])

    self.assertEqual(payment.getSimulationState(), "confirmed")
    self.assertEqual(
        'Transaction status WAITING_AUTHORISATION_TO_VALIDATE did not changed ' \
        'the document state',
        payment.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(
        'Confirmed as really saw in PayZen.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

  def test_processUpdate_notProcessedTransactionStatusConfirmedPayment(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    payment.confirm()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "WAITING_AUTHORISATION_TO_VALIDATE",
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)

  def test_processUpdate_noAuthAmount(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                },
              },
            },
          }
        ],
      },
    }

    self.assertRaises(
      KeyError,
      event.PayzenEvent_processUpdate,
      data_kw)

  def test_processUpdate_noAuthDevise(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": 1,
                },
              },
            },
          }
        ],
      },
    }

    self.assertRaises(
      KeyError,
      event.PayzenEvent_processUpdate,
      data_kw)

  def test_processUpdate_differentAmount(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": 1,
                  "currency": 1,
                },
              },
            },
          }
        ],
      },
    }

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        'Received amount (1) does not match stored on transaction (0)',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_differentDevise(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/EUR',
      start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": 0,
                  "currency": "dollars",
                },
              },
            },
          }
        ],
      },
    }

    self.assertEqual(payment.PaymentTransaction_getTotalPayablePrice(), 0)
    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        "Received devise ('dollars') does not match stored on transaction ('EUR')",
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_cancelledTransaction(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/EUR',
      start_date=DateTime())
    payment.cancel()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": 0,
                  "currency": "EUR",
                },
              },
            },
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "confirmed")
    self.assertEqual(
        'Expected to put transaction in stopped state, but achieved only ' \
        'cancelled state',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  def test_processUpdate_defaultUseCase(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    payment.edit(
      resource='currency_module/EUR',
      start_date=DateTime())
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "AUTHORISED",
            "transactionDetails": {
              "cardDetails": {
                "authorizationResponse": {
                  "amount": 0,
                  "currency": "EUR",
                },
              },
            },
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(payment.getSimulationState(), "stopped")
    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Automatic acknowledge as result of correct communication',
        event.workflow_history['system_event_workflow'][-1]['comment'])

  @simulate("PaymentTransaction_getPayzenId", '*args, **kwargs',
    """return DateTime().toZone('UTC'), 'foo'""")
  def test_processUpdate_recentNotFoundOnPayzenSide(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "ERROR",
      "answer": {
        "errorCode": "PSP_010",
      },
    }
    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Transaction not found on payzen side.',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertNotEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Error code PSP_010 (Not found) did not changed the document state.',
        payment.workflow_history['edit_workflow'][-1]['comment'])

  @simulate("PaymentTransaction_getPayzenId", '*args, **kwargs',
    """from erp5.component.module.DateUtils import addToDate
return addToDate(DateTime(), to_add={'day': -1, 'second': -1}).toZone('UTC'), 'foo'""")
  def test_processUpdate_oldNotFoundOnPayzenSide(self):
    """
    This Test is supposed to Fail as for now we do not want to cancel automatically
    """
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "ERROR",
      "answer": {
        "errorCode": "PSP_010",
      },
    }
    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Transaction not found on payzen side.',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Aborting unknown payzen payment.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

  def test_processUpdate_refusedPayzenPayment(self):
    event = self.createPayzenEvent()
    payment = self.createPaymentTransaction()
    event.edit(destination_value=payment)

    data_kw = {
      "status": "SUCCESS",
      "answer": {
        "transactions": [
          {
            "detailedStatus": "REFUSED",
          }
        ],
      },
    }

    event.PayzenEvent_processUpdate(data_kw)

    self.assertEqual(event.getValidationState(), "acknowledged")
    self.assertEqual(
        'Refused payzen payment.',
        event.workflow_history['system_event_workflow'][-1]['comment'])
    self.assertEqual(payment.getSimulationState(), "cancelled")
    self.assertEqual(
        'Aborting refused payzen payment.',
        payment.workflow_history['accounting_workflow'][-1]['comment'])

class TestSlapOSPayzenBase_getPayzenServiceRelativeUrl(TestSlapOSPayzenMixin):

  def test_getPayzenServiceRelativeUrl_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Base_getPayzenServiceRelativeUrl,
      REQUEST={})

  def test_getPayzenServiceRelativeUrl_default_result(self):
    result = self.portal.Base_getPayzenServiceRelativeUrl()
    self.assertEqual(result, self.payzen_secure_payment.getRelativeUrl())

  def test_getPayzenServiceRelativeUrl_not_found(self):
    self.payzen_secure_payment.setReference("disabled")
    self.tic()
    result = self.portal.Base_getPayzenServiceRelativeUrl()
    self.assertEqual(result, None)


class TestSlapOSPayzenPaymentTransaction_redirectToManualPayzenPayment(
                                                    TestSlapOSPayzenMixin):

  @simulate("PaymentTransaction_getVADSUrlDict", '*args, **kwargs',
  """payment_transaction_url = context.getRelativeUrl()
return dict(vads_url_already_registered="%s/already_registered" % (payment_transaction_url),
  vads_url_cancel="%s/cancel" % (payment_transaction_url),
  vads_url_error="%s/error" % (payment_transaction_url),
  vads_url_referral="%s/referral" % (payment_transaction_url),
  vads_url_refused="%s/refused" % (payment_transaction_url),
  vads_url_success="%s/success" % (payment_transaction_url),
  vads_url_return="%s/return" % (payment_transaction_url),
)""")
  def test_PaymentTransaction_redirectToManualPayzenPayment_unauthorzied(self):
    payment = self.createPaymentTransaction()
    self.logout()
    self.assertRaises(Unauthorized, payment.PaymentTransaction_redirectToManualPayzenPayment)

  @simulate("PaymentTransaction_getVADSUrlDict", '*args, **kwargs',
  """payment_transaction_url = context.getRelativeUrl()
return dict(vads_url_already_registered="%s/already_registered" % (payment_transaction_url),
  vads_url_cancel="%s/cancel" % (payment_transaction_url),
  vads_url_error="%s/error" % (payment_transaction_url),
  vads_url_referral="%s/referral" % (payment_transaction_url),
  vads_url_refused="%s/refused" % (payment_transaction_url),
  vads_url_success="%s/success" % (payment_transaction_url),
  vads_url_return="%s/return" % (payment_transaction_url),
)""") 
  def test_PaymentTransaction_redirectToManualPayzenPayment_redirect(self):
    # Ensure secure payment is consistent
    self.payzen_secure_payment.edit(
      payzen_vads_action_mode='INTERACTIVE',
      payzen_vads_ctx_mode='TEST',
      payzen_vads_page_action='PAYMENT',
      payzen_vads_version='V2',
      link_url_string="https://secure.payzen.eu/vads-payment/",
      service_api_key="A",
      service_password="B",
      service_username="C"
    )

    self.tic()

    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      destination_project_value=project
    )
    self.tic()
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='payzen',
      causality_value=invoice,
      destination_value=invoice.getDestinationValue(),
      destination_section_value=invoice.getDestinationSectionValue(),
      destination_project_value=invoice.getDestinationProjectValue(),
      resource_value=self.portal.currency_module.EUR,
      ledger="automated",
      created_by_builder=1  # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    self.tic()
    self.login(person.getUserId())
    text_content = payment.PaymentTransaction_redirectToManualPayzenPayment()
    
    payment_transaction_url = payment.getRelativeUrl()
    for item in ["vads_site_id",
                 payment_transaction_url,
                 "vads_url_cancel",
                 "%s/cancel" % (payment_transaction_url),
                 "vads_url_error",
                 "%s/error" % (payment_transaction_url),
                 "vads_url_referral",
                 "%s/referral" % (payment_transaction_url),
                 "vads_url_refused",
                 "%s/refused" % (payment_transaction_url),
                 "vads_url_success",
                 "%s/success" % (payment_transaction_url),
                 "vads_url_return",
                 "%s/return" % (payment_transaction_url)]:
      self.assertTrue(item in text_content,
        "%s not in %s" % (item, text_content))
    self.tic()

    system_event_list = payment.getDestinationRelatedValueList(portal_type="Payzen Event")
    self.assertEqual(len(system_event_list), 1)

    self.assertEqual(
      system_event_list[0].getDestinationSection(),
      invoice.getDestinationSection())
    self.assertEqual(
      len(system_event_list[0].contentValues(portal_type="Payzen Event Message")), 1)

  @simulate("PaymentTransaction_getVADSUrlDict", '*args, **kwargs',
  """payment_transaction_url = context.getRelativeUrl()
return dict(vads_url_already_registered="%s/already_registered" % (payment_transaction_url),
  vads_url_cancel="%s/cancel" % (payment_transaction_url),
  vads_url_error="%s/error" % (payment_transaction_url),
  vads_url_referral="%s/referral" % (payment_transaction_url),
  vads_url_refused="%s/refused" % (payment_transaction_url),
  vads_url_success="%s/success" % (payment_transaction_url),
  vads_url_return="%s/return" % (payment_transaction_url),
)""")
  def test_PaymentTransaction_redirectToManualPayzenPayment_already_registered(self):
    project = self.addProject()
    person = self.makePerson(project)
    invoice = self.createStoppedSaleInvoiceTransaction(
      destination_section_value=person,
      destination_project_value=project
    )
    self.tic()
    payment = self.portal.accounting_module.newContent(
      portal_type="Payment Transaction",
      payment_mode='payzen',
      causality_value=invoice,
      destination_value=invoice.getDestinationValue(),
      destination_section_value=invoice.getDestinationSectionValue(),
      destination_project_value=invoice.getDestinationProjectValue(),
      resource_value=self.portal.currency_module.EUR,
      ledger="automated",
      created_by_builder=1 # to prevent init script to create lines
    )
    self.portal.portal_workflow._jumpToStateFor(payment, 'started')

    payment.PaymentTransaction_generatePayzenId()
    self.tic()
    self.login(person.getUserId())
    redirect = payment.PaymentTransaction_redirectToManualPayzenPayment()

    self.assertEqual("%s/already_registered" % payment.getRelativeUrl(),
                      redirect)

    system_event_list = payment.getDestinationRelatedValueList(portal_type="Payzen Event")
    self.assertEqual(len(system_event_list), 0)