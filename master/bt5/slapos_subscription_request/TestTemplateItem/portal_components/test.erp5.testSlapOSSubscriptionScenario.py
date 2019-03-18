# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import changeSkin
from DateTime import DateTime

class TestSlapOSTrialScenario(DefaultScenarioMixin):

  def afterSetUp(self):
    self.login()
    self.portal.portal_alarms.slapos_subscription_request_process_draft.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_ordered.setEnabled(True)
    self.portal.portal_alarms.slapos_subscription_request_process_planned.setEnabled(True)

    DefaultScenarioMixin.afterSetUp(self)

    self.portal.accounting_module.\
      template_pre_payment_subscription_sale_invoice_transaction.\
      updateLocalRolesOnSecurityGroups()

    self.portal.accounting_module.\
      slapos_pre_payment_template.\
       updateLocalRolesOnSecurityGroups()

    # One user to create computers to deploy the subscription
    self.createAdminUser()

    self.createNotificationMessage("subscription_request-confirmation-with-password")
    self.createNotificationMessage("subscription_request-confirmation-without-password",
                               text_content='${name} ${login_name}')
    self.cleanUpSubscriptionRequest()
    self.tic()

  def cleanUpSubscriptionRequest(self):
    for subscription_request in self.portal.portal_catalog(
      portal_type="Subscription Request",
      simulation_state=["draft", "planned", "ordered"],
      title="Test Subscription Request %"):
      if subscription_request.getSimulationState() == "draft":
        subscription_request.cancel()
      if subscription_request.getSimulationState() == "planned":
        subscription_request.order()
      if subscription_request.getSimulationState() == "ordered":
        subscription_request.confirm()

  def createNotificationMessage(self, reference,
      content_type='text/html', text_content='${name} ${login_name} ${login_password}'):

    notification_message = self.portal.notification_message_module.newContent(
      portal_type="Notification Message",
      text_content_substitution_mapping_method_id='NotificationMessage_getSubstitutionMappingDictFromArgument',
      title='TestSubscriptionSkins Notification Message %s' % reference,
      text_content=text_content,
      content_type=content_type,
      reference=reference,
      version=999,
      language="en"
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

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionScenario",
      short_tile="Test Your Scenario",
      description="This is a test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=195.00,
      resource="currency_module/EUR",
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

  def _getRelatedPaymentValue(self, subscription_request):
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    return invoice.getCausalityRelatedValue(portal_type="Payment Transaction")

  def checkAndPayFirstTreeMonth(self, subscription_request):
    self.login()
    person = subscription_request.getDestinationSectionValue()

    quantity = subscription_request.getQuantity()
    self.login(person.getUserId())
    self.usePayzenManually(self.web_site, person.getUserId())

    payment = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      simulation_state="started")

    self.logout()
    self.login()

    # 195 is the month payment
    # 195*3 is the 3 months to pay upfront to use.
    # 25 is the reservation fee deduction.
    data_kw = {
        'errorCode': '0',
        'transactionStatus': '6',
        'authAmount': (19500*3-2500)*quantity,
        'authDevise': '978',
      }
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw, True)

  def checkAndPaySubscriptionPayment(self, subscription_request):
    quantity = subscription_request.getQuantity()
    invoice = subscription_request.getCausalityValue(portal_type="Sale Invoice Transaction")
    self.assertEqual(invoice.getSimulationState(), "confirmed")
    self.assertEqual(invoice.getCausalityState(), "building")

    # Check Payment
    payment = self._getRelatedPaymentValue(subscription_request)
    self.assertEqual(payment.getSimulationState(), "started")

    # Pay 25 euros per VM
    data_kw = {
        'errorCode': '0',
        'transactionStatus': '6',
        'authAmount': 2500*quantity,
        'authDevise': '978',
    }

    # Payzen_processUpdate will mark payment as payed by stopping it.
    payment.PaymentTransaction_createPayzenEvent().PayzenEvent_processUpdate(data_kw, True)
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
    for line in invoice.objectValues():
      if line.getResource() == "service_module/slapos_reservation_fee":
        self.assertEqual(line.getQuantity(), quantity)
        self.assertEqual(round(line.getPrice(), 2), 20.83)
      if line.getResource() == "service_module/slapos_tax":
        self.assertEqual(round(line.getQuantity(), 2), round(20.833333333333333*quantity, 2))
        self.assertEqual(round(line.getTotalPrice(), 2), round(4.166666666666667*quantity, 2))

    self.assertEqual(round(invoice.getTotalPrice(), 2), 25.0*quantity)

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
    mail_message = subscription_request.getFollowUpRelatedValue(
      portal_type="Mail Message")

    self.assertEqual(
      "TestSubscriptionSkins Notification Message %s" % notification_message,
      mail_message.getTitle())
    self.assertTrue(subscription_request.getDefaultEmailText() in \
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
    self.assertEqual(sale_packing_list_line.getQuantity(), 3*quantity)
    self.assertEqual(sale_packing_list_line.getPrice(), 162.50)
    self.assertEqual(sale_packing_list_line.getTotalPrice(), 3*162.50*quantity)

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())

    sale_packing_list_line = [ i for i in sale_packing_list.objectValues()
      if i.getResource() == "service_module/slapos_reservation_refund"][0]

    quantity = subscription_request.getQuantity()
    # The values are without tax
    self.assertEqual(sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(round(sale_packing_list_line.getPrice(), 2), -25*quantity)
    self.assertEqual(round(sale_packing_list_line.getTotalPrice(), 2), -25*quantity)

    self.assertEqual(sale_packing_list.getCausality(),
                     subscription_request.getRelativeUrl())
  @changeSkin('Hal')
  def _requestSubscription(self, **kw):
    return self.web_site.hateoas.SubscriptionRequestModule_requestSubscritption(**kw)

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

  def test_subscription_scenario(self, amount=1):
    """ The admin creates an computer, user can request instances on it"""
    self.login()
    self.createSubscriptionCondition()

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # Call here, We should create the instance in advance...

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

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      amount=amount,
      name=name,
      default_email_text=default_email_text,
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

    # Check if instance was requested
    self.checkRelatedInstance(subscription_request)

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    # Re-check, as instance shouldn't be allocated until
    # the confirmation of the new Payment.
    self.checkRelatedInstance(subscription_request)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateHostingSubscriptionOpenSaleOrderAlarm()
    self.tic()

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

    sale_packing_list_list = self.getAggregatedSalePackingList(
      subscription_request, specialise_subscription_uid)
    self.assertEqual(1, len(sale_packing_list_list))

    self.checkAggregatedSalePackingList(subscription_request, sale_packing_list_list[0])

    self.assertEqual(3, len(self.getSubscriptionSalePackingList(
      subscription_request)))

    self.assertEqual(0, len(self.getAggregatedSalePackingList(
      subscription_request, specialise_uid)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

    self.assertEqual(1, len(self.getAggregatedSalePackingList(
      subscription_request, specialise_subscription_uid)))

    # Call this alarm shouldn't affect the delivery
    self.stepCallSlaposStartConfirmedAggregatedSubscriptionSalePackingListAlarm()
    self.tic()

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
      if len(builder.OrderBuilder_generateUnrelatedInvoiceList()):
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

    self.checkAndPayFirstTreeMonth(subscription_request)
    self.tic()

    # After the payment re-call the Alarm in order to confirm the subscription
    # Request.
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    # Check if instance was already allocated, in this case, it shouldn't
    # until the allocation alarm kicks in.
    self.checkRelatedInstance(subscription_request)

    # Now really allocate the instance
    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    # Re-check, now it should be allocated.
    self.checkAllocationOnRelatedInstance(subscription_request)

  def test_subscription_with_3_vms_scenario(self):
    self.test_subscription_scenario(amount=3)

  def test_two_subscription_scenario(self, amount=1):
    """ The admin creates an computer, user can request instances on it"""
    self.login()
    self.createSubscriptionCondition()

    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # Call here, We should create the instance in advance...

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

    # Call as anonymous... check response?
    default_email_text = "abc%s@nexedi.com" % self.new_id
    name="ABC %s" % self.new_id
    self._requestSubscription(
      subscription_reference=self.subscription_condition.getReference(),
      amount=amount,
      name=name,
      default_email_text=default_email_text,
      REQUEST=self.portal.REQUEST)

    self.login()
    # I'm not sure if this is realistic
    self.tic()

    subscription_request = self.getSubscriptionRequest(
      default_email_text, self.subscription_condition)
    self.checkDraftSubscriptionRequest(subscription_request,
                        default_email_text, self.subscription_condition)

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

    self.logout()
    # Request a second one
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

    subscription_request_list = self.getSubscriptionRequestList(
      default_email_text, self.subscription_condition)
    for subscription_request in subscription_request_list:
      # Check if instance was requested
      self.checkRelatedInstance(subscription_request)

    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    for subscription_request in subscription_request_list:
      # Re-check, as instance shouldn't be allocated until
      # the confirmation of the new Payment.
      self.checkRelatedInstance(subscription_request)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateHostingSubscriptionOpenSaleOrderAlarm()
    self.tic()

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

      self.assertEqual(6, len(self.getSubscriptionSalePackingList(
        subscription_request)))

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
      if len(builder.OrderBuilder_generateUnrelatedInvoiceList()):
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

    for subscription_request in subscription_request_list:
      self.checkAndPayFirstTreeMonth(subscription_request)
      self.tic()

    # After the payment re-call the Alarm in order to confirm the subscription
    # Request.
    self.stepCallSlaposSubscriptionRequestProcessOrderedAlarm()
    self.tic()

    for subscription_request in subscription_request_list:
      # Check if instance was already allocated, in this case, it shouldn't
      # until the allocation alarm kicks in.
      self.checkRelatedInstance(subscription_request)

    # Now really allocate the instance
    self.stepCallSlaposAllocateInstanceAlarm()
    self.tic()

    # now instantiate it on computer and set some nice connection dict
    self.simulateSlapgridCP(subscription_server)
    self.tic()

    for subscription_request in subscription_request_list:
      # Re-check, now it should be allocated.
      self.checkAllocationOnRelatedInstance(subscription_request)

