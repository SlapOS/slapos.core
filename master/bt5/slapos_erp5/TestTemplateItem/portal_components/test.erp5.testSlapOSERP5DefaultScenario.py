# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from DateTime import DateTime
import re

class TestSlapOSDefaultScenario(DefaultScenarioMixin):

  def test_default_scenario(self):
    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # lets join as owner, which will own few computers
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()

    # hooray, now it is time to create computers
    self.login(owner_person.getUserId())

    public_server_title = 'Public Server for %s' % owner_reference
    public_server_id = self.requestComputer(public_server_title)
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=public_server_id)
    self.setAccessToMemcached(public_server)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)

    personal_server_title = 'Personal Server for %s' % owner_reference
    personal_server_id = self.requestComputer(personal_server_title)
    personal_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=personal_server_id)
    self.assertNotEqual(None, personal_server)
    self.setServerOpenPersonal(personal_server)

    friend_server_title = 'Friend Server for %s' % owner_reference
    friend_server_id = self.requestComputer(friend_server_title)
    friend_server = self.portal.portal_catalog.getResultValue(
        portal_type='Computer', reference=friend_server_id)
    self.assertNotEqual(None, friend_server)
    self.setServerOpenFriend(friend_server)

    # and install some software on them
    public_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(public_server, public_server_software)

    personal_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(personal_server, personal_server_software)

    friend_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(friend_server, friend_server_software)

    # format the computers
    self.formatComputer(public_server)
    self.formatComputer(personal_server)
    self.formatComputer(friend_server)


    # join as the another visitor and request software instance on public
    # computer
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    public_instance_type = 'public type'
    self.checkInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        public_server)

    # join as owner friend and request a software instance on computer
    # configured by owner

    self.logout()
    friend_reference = 'friend-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, friend_reference)
    self.login()
    friend_person = self.portal.portal_catalog.getResultValue(
        portal_type='ERP5 Login', reference=friend_reference).getParentValue()
    friend_email = friend_person.getDefaultEmailText()

    # allow friend to alloce on friendly computer
    self.login(owner_person.getUserId())
    self.setServerOpenFriend(friend_server, [friend_email])

    friend_instance_title = 'Friend title %s' % self.generateNewId()
    friend_instance_type = 'friend_type'
    self.checkInstanceAllocation(friend_person.getUserId(), friend_reference,
        friend_instance_title, friend_server_software, friend_instance_type,
        friend_server)

    # check that friend is able to request slave instance matching the
    # public's computer software instance
    friend_slave_instance_title = 'Friend slave title %s' % self.\
        generateNewId()
    self.checkSlaveInstanceAllocation(friend_person.getUserId(),
        friend_reference, friend_slave_instance_title, public_server_software,
        public_instance_type, public_server)

    # turn public guy to a friend and check that he can allocate slave
    # instance on instance provided by friend

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type='ERP5 Login', reference=public_reference).getParentValue()
    public_email = public_person.getDefaultEmailText()
    self.login(owner_person.getUserId())
    self.setServerOpenFriend(friend_server, [friend_email, public_email])

    public_slave_instance_title = 'Public slave title %s' % self\
        .generateNewId()
    self.checkSlaveInstanceAllocation(public_person.getUserId(),
        public_reference, public_slave_instance_title, friend_server_software,
        friend_instance_type, friend_server)

    # now deallocate the slaves
    self.checkSlaveInstanceUnallocation(public_person.getUserId(),
        public_reference, public_slave_instance_title, friend_server_software,
        friend_instance_type, friend_server)

    self.checkSlaveInstanceUnallocation(friend_person.getUserId(),
        friend_reference, friend_slave_instance_title, public_server_software,
        public_instance_type, public_server)

    # and the instances
    self.checkInstanceUnallocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type, public_server)

    self.checkInstanceUnallocation(friend_person.getUserId(),
        friend_reference, friend_instance_title,
        friend_server_software, friend_instance_type, friend_server)

    # and uninstall some software on them
    self.logout()
    self.login(owner_person.getUserId())
    self.supplySoftware(public_server, public_server_software,
                        state='destroyed')
    self.supplySoftware(personal_server, personal_server_software,
                        state='destroyed')
    self.supplySoftware(friend_server, friend_server_software,
                        state='destroyed')

    self.logout()
    # Uninstall from computer
    self.login()
    self.simulateSlapgridSR(public_server)
    self.simulateSlapgridSR(personal_server)
    self.simulateSlapgridSR(friend_server)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateInstanceTreeOpenSaleOrderAlarm()
    self.tic()

    self.login()

    self.assertOpenSaleOrderCoverage(owner_reference)
    self.assertOpenSaleOrderCoverage(friend_reference)
    self.assertOpenSaleOrderCoverage(public_reference)

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

    # start aggregated deliveries
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

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

    # check final document state
    for person_reference in (owner_reference, friend_reference,
        public_reference):
      person = self.portal.portal_catalog.getResultValue(
        portal_type='ERP5 Login', reference=person_reference).getParentValue()
      self.assertPersonDocumentCoverage(person)

    self.login(public_person.getUserId())
    self.usePayzenManually(self.web_site, public_person.getUserId())

    self.login(friend_person.getUserId())
    self.usePayzenManually(self.web_site, friend_person.getUserId())

class TestSlapOSDefaultCRMEscalation(DefaultScenarioMixin):

  def trickCrmEvent(self, service_id, day, person_reference):
    self.login()
    person = self.portal.portal_catalog.getResultValue(portal_type='ERP5 Login',
        reference=person_reference).getParentValue()
    ticket = self.portal.portal_catalog.getResultValue(
        portal_type='Regularisation Request',
        simulation_state='suspended',
        default_source_project_uid=person.getUid()
    )

    event = self.portal.portal_catalog.getResultValue(
      portal_type='Mail Message',
      default_resource_uid=self.portal.service_module[service_id].getUid(),
      default_follow_up_uid=ticket.getUid(),
    )
    event.edit(start_date=event.getStartDate()-day)
    data = event.getData()
    data = re.sub(
      "\nDate: .*\n",
      "\nDate: %s\n" % (event.getStartDate()-day).rfc822(),
      data)
    event.edit(data=data)

  def assertOpenSaleOrderCoverage(self, person_reference):
    self.login()
    person = self.portal.portal_catalog.getResultValue(
       portal_type='ERP5 Login',
       reference=person_reference).getParentValue()
    instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        default_destination_section_uid=person.getUid()
    )

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid(),
    )

    if len(instance_tree_list) == 0:
      self.assertEqual(0, len(open_sale_order_list))
      return

    self.assertEqual(1, len(open_sale_order_list))

    open_sale_order = open_sale_order_list[0]
    line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(len(instance_tree_list), len(line_list))
    self.assertSameSet(
        [q.getRelativeUrl() for q in instance_tree_list],
        [q.getAggregate() for q in line_list]
    )

  def assertAggregatedSalePackingList(self, delivery):
    self.assertEqual('delivered', delivery.getSimulationState())
    self.assertEqual('solved', delivery.getCausalityState())

    invoice_list= delivery.getCausalityRelatedValueList(
        portal_type='Sale Invoice Transaction')
    self.assertEqual(1, len(invoice_list))
    invoice = invoice_list[0].getObject()

    causality_list = invoice.getCausalityValueList()

    self.assertSameSet([delivery], causality_list)

    self.assertEqual('stopped', invoice.getSimulationState())
    self.assertEqual('solved', invoice.getCausalityState())

    payment_list = invoice.getCausalityRelatedValueList(
        portal_type='Payment Transaction')
    self.assertEqual(1, len(payment_list))

    payment = payment_list[0].getObject()

    causality_list = payment.getCausalityValueList()
    self.assertSameSet([invoice], causality_list)

    self.assertEqual('cancelled', payment.getSimulationState())
    self.assertEqual('draft', payment.getCausalityState())

    self.assertEqual(-1 * payment.PaymentTransaction_getTotalPayablePrice(),
        invoice.getTotalPrice())

    # Check reverse invoice
    reverse_invoice_list = invoice.getCausalityRelatedValueList(
        portal_type='Sale Invoice Transaction')
    self.assertEqual(1, len(reverse_invoice_list))

    reverse_invoice = reverse_invoice_list[0].getObject()

    causality_list = reverse_invoice.getCausalityValueList()
    self.assertSameSet([invoice], causality_list)

    self.assertEqual('stopped', reverse_invoice.getSimulationState())
    self.assertEqual('draft', reverse_invoice.getCausalityState())

    payment_list = reverse_invoice.getCausalityRelatedValueList(
        portal_type='Payment Transaction')
    self.assertEqual(0, len(payment_list))

  def test_crm_escalation(self):
    # some preparation
    self.logout()
    self.web_site = self.portal.web_site_module.hostingjs

    # join as the another visitor and request software instance on public
    # computer
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    self.tic()
    person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login", reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    public_instance_type = 'public type'
    public_server_software = self.generateNewSoftwareReleaseUrl()
    self.requestInstance(person.getUserId(), public_instance_title,
        public_server_software, public_instance_type)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateInstanceTreeOpenSaleOrderAlarm()
    self.tic()

    self.login()

    self.assertOpenSaleOrderCoverage(public_reference)

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

    # start aggregated deliveries
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

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

    # create the regularisation request
    self.stepCallSlaposCrmCreateRegularisationRequestAlarm()
    self.tic()

    # escalate 1
    self.trickCrmEvent('slapos_crm_acknowledgement', 15, public_reference)
    self.stepCallSlaposCrmTriggerAcknowledgmentEscalationAlarm()
    self.tic()

    # escalate 2
    self.trickCrmEvent('slapos_crm_stop_reminder', 7, public_reference)
    self.stepCallSlaposCrmTriggerStopReminderEscalationAlarm()
    self.tic()

    # stop the subscription
    self.stepCallSlaposCrmStopInstanceTreeAlarm()
    self.tic()
    self.assertSubscriptionStopped(person)

    # escalate 3
    self.trickCrmEvent('slapos_crm_stop_acknowledgement', 7, public_reference)
    self.stepCallSlaposCrmTriggerStopAcknowledgmentEscalationAlarm()
    self.tic()

    # escalate 4
    self.trickCrmEvent('slapos_crm_delete_reminder', 10, public_reference)
    self.stepCallSlaposCrmTriggerDeleteReminderEscalationAlarm()
    self.tic()

    # delete the subscription
    self.stepCallSlaposCrmDeleteInstanceTreeAlarm()
    self.tic()
    self.assertSubscriptionDestroyed(person)

    # check the Open Sale Order coverage
    self.stepCallSlaposRequestUpdateInstanceTreeOpenSaleOrderAlarm()
    self.tic()


    # Manually cancel the users invoice
    payment = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      destination_section_uid=person.getUid(),
      simulation_state="started")

    invoice = payment.getCausalityValue(portal_type="Sale Invoice Transaction")
    invoice.SaleInvoiceTransaction_createReversalPayzenTransaction()

    self.tic()

    # close the ticket
    self.stepCallSlaposCrmInvalidateSuspendedRegularisationRequestAlarm()
    self.tic()

    # update open order simulation
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

    # start aggregated deliveries
    self.stepCallSlaposStartConfirmedAggregatedSalePackingListAlarm(
        accounting_date=DateTime('2222/01/01'))
    self.tic()

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

    # check final document state
    self.assertPersonDocumentCoverage(person)
