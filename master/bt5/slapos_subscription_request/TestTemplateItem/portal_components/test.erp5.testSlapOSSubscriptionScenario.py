# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
from DateTime import DateTime

class TestSlapOSSubscriptionScenarioMixin(DefaultScenarioMixin):

  def afterSetUp(self):
    self.normal_user = None
    self.expected_individual_price_without_tax = 162.50
    self.expected_individual_price_with_tax = 195.00
    self.expected_reservation_fee = 25.00
    self.expected_reservation_fee_without_tax = 20.83
    self.expected_reservation_quantity_tax = 20.833333333333333
    self.expected_reservation_tax = 4.166666666666667
    self.expected_price_currency = "currency_module/EUR"
    self.expected_notification_language = "en"
    self.expected_source = "organisation_module/slapos"
    self.expected_source_section = "organisation_module/slapos"
    
    self.login()
    self.portal.portal_alarms.slapos_subscription_request_process_draft.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_ordered.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_planned.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_confirmed.setEnabled(True)

    DefaultScenarioMixin.afterSetUp(self)

    self.portal.accounting_module.\
      template_pre_payment_subscription_sale_invoice_transaction.\
      updateLocalRolesOnSecurityGroups()

    self.portal.accounting_module.\
      slapos_pre_payment_template.\
       updateLocalRolesOnSecurityGroups()

    # One user to create computers to deploy the subscription
    self.createAdminUser()
    self.cleanUpNotificationMessage()
    self.tic()
    
    self.createNotificationMessage("subscription_request-confirmation-with-password")
    self.createNotificationMessage("subscription_request-confirmation-without-password",
                               text_content='${name} ${login_name}')
    self.createNotificationMessage("subscription_request-instance-is-ready", 
      text_content='${name} ${subscription_title} ${hosting_subscription_relative_url}')
    self.createNotificationMessage("subscription_request-payment-is-ready",
      text_content='${name} ${subscription_title} ${payment_relative_relative_url}')
    
    self.cleanUpSubscriptionRequest()
    self.tic()
    
    self.login()
    self.createSubscriptionCondition()

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

  def cleanUpSubscriptionRequest(self):
    for subscription_request in self.portal.portal_catalog(
      portal_type="Subscription Request",
      simulation_state=["draft", "planned", "ordered", "confirmed"],
      title="Test Subscription Request %"):
      if subscription_request.getSimulationState() == "draft":
        subscription_request.cancel()
      if subscription_request.getSimulationState() == "planned":
        subscription_request.order()
      if subscription_request.getSimulationState() == "ordered":
        subscription_request.confirm()
      if subscription_request.getSimulationState() == "confirmed":
        subscription_request.start()
      if subscription_request.getSimulationState() == "started":
        subscription_request.stop()

  def cleanUpNotificationMessage(self):
    for notification_message in self.portal.portal_catalog(
      portal_type="Notification Message",
      validation_state=["validated"],
      title="TestSubscriptionSkins %"):
      if str(notification_message.getVersion("")) == "999":
        notification_message.invalidate()

  def createNotificationMessage(self, reference,
      content_type='text/html', language="en", text_content='${name} ${login_name} ${login_password}'):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s %s' % (language, reference),
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language=language
      )
    notification_message.validate()
    return notification_message

  def createAdminUser(self):
    """ Create a Admin user, to manage computers and instances eventually """
    admin_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference="admin_user",
      validation_state="validated"
    )

    if admin_user_login is None:
      admin_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)

      admin_user.newContent(
        portal_type="ERP5 Login",
        reference="admin_user").validate()

      admin_user.edit(
        first_name="Admin User",
        reference="Admin_user",
        default_email_text="do_not_reply_to_admin@example.org",
      )

      for assignment in admin_user.contentValues(portal_type="Assignment"):
        assignment.open()

      admin_user.validate()
      self.admin_user = admin_user
    else:
      self.admin_user = admin_user_login.getParentValue()

  def createNormalUser(self, email, name, language):
    """ Create a Normal user """
    normal_user_login = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=email,
      validation_state="validated"
    )

    if normal_user_login is None:
      normal_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)

      normal_user.newContent(
        portal_type="ERP5 Login",
        reference=email).validate()

      normal_user.edit(
        first_name=name,
        reference=email,
        default_email_text=email,
      )

      for assignment in normal_user.contentValues(portal_type="Assignment"):
        assignment.open()

      normal_user.validate()
      self.normal_user = normal_user
    else:
      self.normal_user = normal_user_login.getParentValue()
    self.normal_user.setLanguage(language)

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionScenario",
      short_tile="Test Your Scenario",
      description="This is a test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=195.00,
      price_currency="currency_module/EUR",
      default_source_reference="default",
      reference="rapidvm%s" % self.new_id,
      # Aggregate and Follow up to web pages for product description and
      # Terms of service
      sla_xml='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      text_content='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      user_input={}
    )
    self.subscription_condition.validate()
    self.subscription_condition.updateLocalRolesOnSecurityGroups()
    self.tic()

  def getSubscriptionRequest(self, email, subscription_condition):
    subscription_request_list = subscription_condition.getSpecialiseRelatedValueList(
              portal_type='Subscription Request')
    self.assertEqual(len(subscription_request_list), 1)
    return subscription_request_list[0]

  def getSubscriptionRequestList(self, email, subscription_condition):
    subscription_request_list = subscription_condition.getSpecialiseRelatedValueList(
              portal_type='Subscription Request')
    return subscription_request_list

  def checkSubscriptionRequest(self, subscription_request, email, subscription_condition, slave=0):
    self.assertNotEqual(subscription_request, None)
    self.assertEqual(subscription_request.getDefaultEmailText(), email)
    self.assertEqual(subscription_request.getUrlString(), subscription_condition.getUrlString())
    self.assertEqual(subscription_request.getRootSlave(), slave)
    self.assertEqual(subscription_request.getTextContent(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(trial_request.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(subscription_request.getSourceReference(), "default")

  def checkDraftSubscriptionRequest(self, subscription_request, email, subscription_condition,
                                      slave=0, amount=1):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition, slave=slave)
    # XXX This might be diferent
    self.assertEqual(subscription_request.getQuantity(), amount)

    self.assertEqual(subscription_request.getAggregate(), None)
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    self.assertNotEqual(invoice, None)
    payment = invoice.getCausalityRelatedValue(portal_type="Payment Transaction")
    self.assertNotEqual(payment, None)

  def checkPlannedSubscriptionRequest(self, subscription_request, email, subscription_condition, slave=0):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition, slave=slave)
    self.assertEqual(subscription_request.getSimulationState(), "planned")


  def checkOrderedSubscriptionRequest(self, subscription_request, email, subscription_condition, slave=0,
                                        notification_message="subscription_request-confirmation-with-password"):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition, slave=slave)
    self.assertEqual(subscription_request.getSimulationState(), "ordered")
    self.checkBootstrapUser(subscription_request)
    self.checkEmailNotification(subscription_request, notification_message)

  def checkConfirmedSubscriptionRequest(self, subscription_request, email, subscription_condition, slave=0,
                                        notification_message="subscription_request-payment-is-ready"):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition, slave=slave)
    payment = subscription_request.SubscriptionRequest_verifyPaymentBalanceIsReady()
    self.assertNotEqual(payment, None)
    self.assertEqual(payment.getSimulationState(), 'started')
    self.assertEqual(subscription_request.getSimulationState(), "confirmed")
    self.checkEmailPaymentNotification(subscription_request, notification_message)

  def checkStartedSubscriptionRequest(self, subscription_request, email, subscription_condition, slave=0,
                                        notification_message="subscription_request-instance-is-ready"):
    self.checkSubscriptionRequest(subscription_request, email, subscription_condition, slave=slave)
    self.assertEqual(subscription_request.getSimulationState(), "started")
    self.checkEmailInstanceNotification(subscription_request, notification_message)

  def _getRelatedPaymentValue(self, subscription_request):
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    return invoice.getCausalityRelatedValue(portal_type="Payment Transaction")

  def createReversalInvoiceAndCancelPayment(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()
    self.login(person.getUserId())

    payment = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      simulation_state="started")

    sale_transaction_invoice = payment.getCausalityValue(
      portal_type="Sale Invoice Transaction"
    )

    self.logout()
    self.login()
    sale_transaction_invoice.SaleInvoiceTransaction_createReversalPayzenTransaction()

  def checkAndPayFirstMonth(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()

    quantity = subscription_request.getQuantity()
    self.login(person.getUserId())
    self.usePayzenManually(self.web_site, person.getUserId())

    payment = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      simulation_state="started")

    # 195 is the month payment
    # 195*1 is the 1 months to pay upfront to use.
    # 25 is the reservation fee deduction.
    authAmount = (int(self.expected_individual_price_with_tax*100)*1-int(self.expected_reservation_fee*100))*quantity

    self.assertEqual(payment.getSourceSection(), self.expected_source_section)
    self.assertEqual(payment.getSourcePayment(), "%s/bank_account" % self.expected_source_section)
    

    self.assertEqual(int(payment.PaymentTransaction_getTotalPayablePrice()*100),
                     -authAmount)
    
    self.assertEqual(payment.getPriceCurrency(), self.expected_price_currency)

    self.logout()
    self.login()

    data_kw = {
        'errorCode': '0',
        'transactionStatus': '6',
        'authAmount': authAmount,
        'authDevise': '978',
      }
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw, True)

  def _payPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    # Check Payment
    payment = self._getRelatedPaymentValue(subscription_request)

    self.assertEqual(self.expected_price_currency, payment.getPriceCurrency())
    self.assertEqual(-self.expected_reservation_fee*quantity,
      payment.PaymentTransaction_getTotalPayablePrice())
    
    self.assertEqual(payment.getSimulationState(), "started")

    # Pay 25 euros per VM
    data_kw = {
        'errorCode': '0',
        'transactionStatus': '6',
        'authAmount': self.expected_reservation_fee*100*quantity,
        'authDevise': '978',
    }

    # Payzen_processUpdate will mark payment as payed by stopping it.
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw, True)
    return payment
 
  def checkAndPaySubscriptionPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    invoice = subscription_request.getCausalityValue(
      portal_type="Sale Invoice Transaction")
    self.assertEqual(invoice.getSimulationState(), "confirmed")
    self.assertEqual(invoice.getCausalityState(), "building")

    self.assertEqual(invoice.getSource(), self.expected_source)
    self.assertEqual(invoice.getSourceSection(), self.expected_source_section)
    
    # Check Payment
    payment = self._payPayment(subscription_request)
    self.assertEqual(payment.getSourceSection(), self.expected_source_section)
    self.assertEqual(payment.getSourcePayment(), "%s/bank_account" % self.expected_source_section)
    
    self.tic()
    self.assertEqual(payment.getSimulationState(), "stopped")

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    self.assertEqual(invoice.getSimulationState(), "stopped")
    self.assertEqual(invoice.getCausalityState(), "solved")
    self.assertEqual(invoice.getPriceCurrency(), self.expected_price_currency)
    for line in invoice.objectValues():
      if line.getResource() == "service_module/slapos_reservation_fee":
        self.assertEqual(line.getQuantity(), quantity)
        self.assertEqual(round(line.getPrice(), 2),  self.expected_reservation_fee_without_tax)
      if line.getResource() == "service_module/slapos_tax":
        self.assertEqual(round(line.getQuantity(), 2), round(self.expected_reservation_quantity_tax*quantity, 2))
        self.assertEqual(round(line.getTotalPrice(), 2), round(self.expected_reservation_tax*quantity, 2))

    self.assertEqual(round(invoice.getTotalPrice(), 2), self.expected_reservation_fee*quantity)

  def checkBootstrapUser(self, subscription_request):
    person = subscription_request.getDestinationSectionValue(portal_type="Person")
    self.assertEqual(person.getDefaultEmailText(),
                     subscription_request.getDefaultEmailText())
    self.assertEqual(person.getValidationState(), "validated")

    login_list = [x for x in person.objectValues(portal_type='ERP5 Login') \
              if x.getValidationState() == 'validated']

    self.assertEqual(len(login_list), 1)
    self.assertEqual(login_list[0].getReference(), person.getDefaultEmailText())
    self.assertSameSet(person.getRoleList(), ["member", "subscriber"])

  def checkEmailNotification(self, subscription_request,
                 notification_message="subscription_request-confirmation-with-password"):
    expected_amount = 1
    if self.normal_user is not None:
      # If user already exists we do not expect to send an email
      expected_amount = 0
    
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), expected_amount)
    if not expected_amount:
      return

    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (self.expected_notification_language, notification_message),
      mail_message.getTitle())
    self.assertTrue(subscription_request.getDefaultEmailText() in \
                 mail_message.getTextContent())
    self.assertTrue(subscription_request.getDestinationSectionTitle() in \
      mail_message.getTextContent())

  def checkEmailPaymentNotification(self, subscription_request,
                 notification_message="subscription_request-payment-is-ready"):
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), 1)
    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (self.expected_notification_language, notification_message),
      mail_message.getTitle())
    payment = subscription_request.SubscriptionRequest_verifyPaymentBalanceIsReady()
    self.assertEqual(payment.getSimulationState(), 'started')
    invoice = payment.getCausalityValue()
    self.assertTrue(invoice.getRelativeUrl() in \
                 mail_message.getTextContent())
    self.assertTrue(subscription_request.getDestinationSectionTitle() in \
      mail_message.getTextContent())

  def checkEmailInstanceNotification(self, subscription_request,
                 notification_message="subscription_request-instance-is-ready"):
    mail_message_list = [i for i in subscription_request.getFollowUpRelatedValueList(
      portal_type="Mail Message") if notification_message in i.getTitle()]

    self.assertEqual(len(mail_message_list), 1)
    mail_message = mail_message_list[0]
    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s %s" % (self.expected_notification_language, notification_message),
      mail_message.getTitle())
    hosting_subscription = subscription_request.getAggregateValue()
    self.assertEqual(hosting_subscription.getSlapState(), 'start_requested')
    self.assertTrue(hosting_subscription.getRelativeUrl() in \
                 mail_message.getTextContent())
    self.assertTrue(subscription_request.getDestinationSectionTitle() in \
      mail_message.getTextContent())

  def checkRelatedInstance(self, subscription_request):
    instance = self._checkRelatedInstance(subscription_request)
    self.assertEqual(instance.getAggregate(), None)

  def _checkRelatedInstance(self, subscription_request):
    hosting_subscription = subscription_request.getAggregateValue()
    self.assertNotEqual(hosting_subscription, None)

    self.assertEqual(subscription_request.getUrlString(),
                     hosting_subscription.getUrlString())
    self.assertEqual(subscription_request.getRootSlave(),
                     hosting_subscription.getRootSlave())
    self.assertEqual(hosting_subscription.getTextContent(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    #self.assertEqual(trial_request.getSlaXml(), '<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>')
    self.assertEqual(hosting_subscription.getSourceReference(), "default")

    instance_list = hosting_subscription.getSpecialiseRelatedValueList(
              portal_type=["Software Instance", "Slave Instace"])
    self.assertEqual(1,len(instance_list))

    return instance_list[0]

  def checkAllocationOnRelatedInstance(self, subscription_request):
    instance = self._checkRelatedInstance(subscription_request)
    self.assertNotEqual(instance.getAggregate(), None)

  def checkAggregatedSalePackingList(self, subscription_request, sale_packing_list):
    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_instance_subscription"][0]

    quantity = subscription_request.getQuantity()
    # The values are without tax
    self.assertEqual(sale_packing_list_line.getQuantity(), 1*quantity)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2),
      round(self.expected_individual_price_without_tax, 2))
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2), 
      round(1*self.expected_individual_price_without_tax*quantity, 2))

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_reservation_refund"][0]

    quantity = subscription_request.getQuantity()
    # The values are without tax
    self.assertEqual(sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2), -int(self.expected_reservation_fee*quantity))
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2), -int(self.expected_reservation_fee*quantity))

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    self.assertEqual(sale_packing_list.getPriceCurrency(),
                     self.expected_price_currency)

  @changeSkin('Hal')
  def _requestSubscription(self, **kw):
    return self.web_site.hateoas.SubscriptionRequestModule_requestSubscription(**kw)

  def getAggregatedSalePackingList(self, subscription_request, specialise):
    person_uid = subscription_request.getDestinationSectionValue().getUid()
    specialise_uid = self.portal.restrictedTraverse(specialise).getUid()

    return self.portal.portal_catalog(
      portal_type='Sale Packing List',
      simulation_state='confirmed',
      causality_state='solved',
      causality_uid=subscription_request.getUid(),
      destination_decision_uid=person_uid,
      specialise_uid=specialise_uid)

  def getSubscriptionSalePackingList(self, subscription_request):
    person_uid = subscription_request.getDestinationSectionValue().getUid()
    specialise_uid = self.portal.restrictedTraverse(
      "sale_trade_condition_module/slapos_subscription_trade_condition").getUid()

    return self.portal.portal_catalog(
      portal_type='Sale Packing List',
      simulation_state='delivered',
      causality_state='solved',
      destination_decision_uid=person_uid,
      specialise_uid=specialise_uid)

  def createPublicServerForAdminUser(self):
    # hooray, now it is time to create computers
    self.login(self.admin_user.getUserId())

    # Create a Public Server for admin user, and allow
    subscription_server_title = 'Trial Public Server for Admin User %s' % self.new_id
    subscription_server_id = self.requestComputer(subscription_server_title)
    subscription_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=subscription_server_id)
    self.setAccessToMemcached(subscription_server)
    self.assertNotEqual(None, subscription_server)
    self.setServerOpenSubscription(subscription_server)

    # and install some software on them
    subscription_server_software = self.subscription_condition.getUrlString()
    self.supplySoftware(subscription_server, subscription_server_software)

    # format the computers
    self.formatComputer(subscription_server)

    self.tic()
    self.logout()
    return subscription_server

  def requestAndCheckHostingSubscription(self, amount, name, 
              default_email_text):
  
    self.logout()
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      amount=amount,
      name=name,
      default_email_text=default_email_text,
      confirmation_required=False,
      REQUEST=self.portal.REQUEST)

    self.login()
    # I'm not sure if this is realistic
    self.tic()

    subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)
    self.checkDraftSubscriptionRequest(subscription_request,
                      default_email_text, self.subscription_condition, amount=amount)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment(subscription_request)
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to make the request of the instance?
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    sale_packing_list_list = self.portal.portal_catalog(
      causality_uid = subscription_request.getUid(),
      title="Reservation Deduction",
      portal_type="Sale Packing List"
    )
    self.assertEqual(len(sale_packing_list_list), 1)
    sale_packing_list = sale_packing_list_list[0]

    self.assertEqual(sale_packing_list.getPriceCurrency(),
                     self.expected_price_currency)
    self.assertEqual(sale_packing_list.getSpecialise(),
      "sale_trade_condition_module/slapos_reservation_refund_trade_condition")

    self.assertEqual(round(sale_packing_list.getTotalPrice(), 2),
                     -round(self.expected_reservation_fee*amount, 2))

    return subscription_request

  def _checkSubscriptionDeploymentAndSimulation(self, subscription_request_list,
                                                default_email_text, subscription_server):

    for subscription_request in subscription_request_list:
      # Check if instance was requested
      self.checkRelatedInstance(subscription_request)

    self.simulateSlapgridCP(subscription_server)
    self.tic()

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    for subscription_request in subscription_request_list:
      # Re-check, as instance shouldn't be allocated until
      # the confirmation of the new Payment.
      self.checkAllocationOnRelatedInstance(subscription_request)

    # generate simulation for open order
    self.stepCallUpdateOpenOrderSimulationAlarm()
    self.tic()

    # build subscription packing list
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise build deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated packing list
    self.stepCallSlaposTriggerAggregatedDeliveryOrderBuilderAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # check if Packing list is generated with the right trade condition
    preference_tool = self.portal.portal_preferences
    specialise_subscription_uid = preference_tool.getPreferredAggregatedSubscriptionSaleTradeCondition()
    specialise_uid = preference_tool.getPreferredAggregatedSaleTradeCondition()

    for subscription_request in subscription_request_list:
      sale_packing_list_list = self.getAggregatedSalePackingList(
        subscription_request, specialise_subscription_uid)
      self.assertEqual(1, len(sale_packing_list_list))

      self.checkAggregatedSalePackingList(subscription_request, sale_packing_list_list[0])

      expected_sale_packing_list_amount = len(subscription_request_list) * 1
      self.assertEqual(expected_sale_packing_list_amount, 
        len(self.getSubscriptionSalePackingList(subscription_request)))

      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, specialise_uid)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(1, len(self.getAggregatedSalePackingList(
        subscription_request, specialise_subscription_uid)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSubscriptionSalePackingListAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertEqual(0, len(self.getAggregatedSalePackingList(
        subscription_request, specialise_uid)))

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # deliver aggregated deliveries
    self.stepCallSlaposDeliverStartedAggregatedSalePackingListAlarm()
    self.tic()

    # stabilise aggregated deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # build aggregated invoices
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()

    # stabilise aggregated invoices and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # update invoices with their tax & discount transaction lines
    self.stepCallSlaposTriggerBuildAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # stop the invoices and solve them again
    self.stepCallSlaposStopConfirmedAggregatedSaleInvoiceTransactionAlarm()
    self.tic()
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    builder = self.portal.portal_orders.slapos_payment_transaction_builder
    for _ in range(500):
      # build the aggregated payment
      self.stepCallSlaposTriggerPaymentTransactionOrderBuilderAlarm()
      self.tic()
      # If there is something unbuild recall alarm.
      if not len(builder.OrderBuilder_generateUnrelatedInvoiceList()):
        break

    # start the payzen payment
    self.stepCallSlaposPayzenUpdateConfirmedPaymentAlarm()
    self.tic()

    # stabilise the payment deliveries and expand them
    self.stepCallSlaposManageBuildingCalculatingDeliveryAlarm()
    self.tic()

    # trigger the CRM interaction
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    # After the payment re-call the Alarm in order to confirm the subscription
    # Request.
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      # Instances should be allocated
      self.checkAllocationOnRelatedInstance(subscription_request)

    # Check if instance is on confirmed state
    for subscription_request in subscription_request_list:
      self.checkConfirmedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)
      
      # Assert that First month isn't payed
      self.assertFalse(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEquals('start_requested',
        subscription_request.getAggregateValue().getSlapState())
      
    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertFalse(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEquals('stop_requested',
        subscription_request.getAggregateValue().getSlapState())

  def checkSubscriptionDeploymentAndSimulationWithReversalTransaction(self, default_email_text, subscription_server):
    
    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    self._checkSubscriptionDeploymentAndSimulation(
      subscription_request_list, default_email_text, subscription_server)

    # Make payments and reinvoke alarm
    for subscription_request in subscription_request_list:
      self.createReversalInvoiceAndCancelPayment(subscription_request)
      self.tic()

    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      # It is requireds a second interaction so the instance is 
      # correctly started
      self.assertEqual("confirmed", subscription_request.getSimulationState())

    # On the second loop that email is send and state is moved to started
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEquals('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      self.checkStartedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)
    


  def checkSubscriptionDeploymentAndSimulation(self, default_email_text, subscription_server):
    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)

    self._checkSubscriptionDeploymentAndSimulation(
      subscription_request_list, default_email_text, subscription_server)

    for subscription_request in subscription_request_list:
      self.checkAndPayFirstMonth(subscription_request)
      self.tic()
    
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEqual('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      # It is requireds a second interaction so the instance is 
      # correctly started
      self.assertEqual("confirmed", subscription_request.getSimulationState())

    # On the second loop that email is send and state is moved to started
    self.stepCallSlaposSubscriptionRequestProcessConfirmedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      self.assertTrue(
        subscription_request.SubscriptionRequest_testPaymentBalance())
      
      self.assertEquals('start_requested',
        subscription_request.getAggregateValue().getSlapState())

      self.checkStartedSubscriptionRequest(subscription_request,
               default_email_text, self.subscription_condition)
    
  def _test_subscription_scenario(self, amount=1):
    """ The admin creates an computer, user can request instances on it"""

    subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.requestAndCheckHostingSubscription(
      amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, subscription_server)

  def _test_subscription_scenario_with_existing_user(self, amount=1, language=None):
    """ The admin creates an computer, user can request instances on it"""

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.login()
    self.createNormalUser(default_email_text, name, language)
    self.tic()

    subscription_server = self.createPublicServerForAdminUser()

    self.requestAndCheckHostingSubscription(
      amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, subscription_server)

    subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)

    self.assertEqual(self.normal_user,
                    subscription_request.getDestinationSectionValue())


  def _test_two_subscription_scenario(self, amount=1):
    """ The admin creates an computer, user can request instances on it"""
 
    subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id

    self.logout()
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      amount=amount,
      name=name,
      default_email_text=default_email_text,
      REQUEST=self.portal.REQUEST)

    self.login()

    # I'm not sure if this is realistic
    self.tic()

    first_subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)

    self.checkDraftSubscriptionRequest(first_subscription_request,
                      default_email_text, self.subscription_condition, amount=amount)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment(first_subscription_request)
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(first_subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(first_subscription_request,
               default_email_text, self.subscription_condition)

    self.logout()
    # Request a second one, without require confirmation and verifing the second subscription request
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      amount=amount,
      name=name,
      default_email_text=default_email_text,
      confirmation_required=False,
      REQUEST=self.portal.REQUEST)

    self.login()
    self.tic()
    second_subscription_request = [ i for i in self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition) if i.getSimulationState() == "draft"][0]

    self.checkDraftSubscriptionRequest(second_subscription_request,
                        default_email_text, self.subscription_condition)

    # Check Payment and pay it.
    self.checkAndPaySubscriptionPayment(second_subscription_request)
    self.tic()

    # Call alarm to check payment and invoice and move foward to planned.
    self.stepCallSlaposSubscriptionRequestProcessDraftAlarm()
    self.tic()

    self.checkPlannedSubscriptionRequest(second_subscription_request,
               default_email_text, self.subscription_condition)

    # Call alarm to mark subscription request as ordered, bootstrap the user
    # and check if email is sent, once done move to ordered state.
    self.stepCallSlaposSubscriptionRequestProcessPlannedAlarm()
    self.tic()

    self.checkOrderedSubscriptionRequest(second_subscription_request,
               default_email_text, self.subscription_condition,
               notification_message="subscription_request-confirmation-without-password")

    # Call alarm to make the request of the instance?
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # The alarms might be called multiple times for move each step
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    self.checkSubscriptionDeploymentAndSimulation(
        default_email_text, subscription_server)


  def _test_subscription_scenario_with_reversal_transaction(self, amount=1):
    """ The admin creates an computer, user can request instances on it"""

    subscription_server = self.createPublicServerForAdminUser()

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    self.requestAndCheckHostingSubscription(amount, name, default_email_text)

    self.checkSubscriptionDeploymentAndSimulationWithReversalTransaction(
        default_email_text, subscription_server)


class TestSlapOSSubscriptionScenario(TestSlapOSSubscriptionScenarioMixin):

  def test_subscription_scenario_with_single_vm(self):
    self._test_subscription_scenario(amount=1)

  def test_subscription_scenario_with_reversal_transaction(self):
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_subscription_with_3_vms_scenario(self):
    self._test_subscription_scenario(amount=3)

  def test_two_subscription_scenario(self):
    self._test_two_subscription_scenario(amount=1)

  def test_subscription_scenario_with_existing_user(self):
    self._test_subscription_scenario_with_existing_user(amount=1, language="en")

  def test_subscription_scenario_with_existing_chinese_user(self):
    # Messages are in english, when subscribed via english website. Even if the chinese language is
    # defined at user level.
    self._test_subscription_scenario_with_existing_user(amount=1, language="zh")
