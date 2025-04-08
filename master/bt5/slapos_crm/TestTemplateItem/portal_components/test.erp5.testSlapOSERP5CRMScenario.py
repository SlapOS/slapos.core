# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSCRMScenario(TestSlapOSVirtualMasterScenarioMixin):

  def afterSetUp(self):
    TestSlapOSVirtualMasterScenarioMixin.afterSetUp(self)

    # Ensure that the required alarms are enabled, else things dont work.
    for required_alarm_id in ['slapos_crm_create_regularisation_request',
                              'slapos_crm_invalidate_suspended_regularisation_request',
                              'slapos_crm_trigger_stop_reminder_escalation',
                              'slapos_crm_trigger_stop_acknowledgment_escalation',
                              'slapos_crm_trigger_delete_reminder_escalation',
                              'slapos_crm_trigger_acknowledgment_escalation',
                              'slapos_crm_stop_instance_tree',
                              'slapos_crm_delete_instance_tree']:
      self.assertTrue(
        self.portal.portal_alarms[required_alarm_id].isEnabled(),
        "%s alarm is not enabled" % required_alarm_id)

  def bootstrapCRMScenario(self, creation_date):
    with PinnedDateTime(self, creation_date):
      owner_person, currency, project = self.bootstrapAccountingTest()
      # Create software product
      software_release_url = self.generateNewSoftwareReleaseUrl()
      software_type = 'public type'
      software_product, _, _ = self.addSoftwareProduct(
        "instance product", project, software_release_url, software_type
      )
      self.tic()
      sale_supply = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Supply',
        source_project__uid=project.getUid()
      )
      sale_supply.searchFolder(
        portal_type='Sale Supply Line',
        resource__relative_url="service_module/slapos_compute_node_subscription"
      )[0].edit(base_price=7)
      # Create supply to buy services
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=6,
        resource_value=software_product
      )
      sale_supply.validate()
      self.tic()
    # Ensure no unexpected object has been created
    # 2 assignment
    # 2 sale trade condition
    # 1 subscription requests
    # 1 software product
    # 3 sale supply + lines
    self.assertRelatedObjectCount(project, 9)

    ##################################################
    # Add deposit
    with PinnedDateTime(self, creation_date):
      # Pay deposit to validate virtual master
      self.login(owner_person.getUserId())
      deposit_amount = 42.0
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)

      # Ensure to pay from the website
      outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
      outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

      self.tic()
      self.logout()
      self.login()
      payment_transaction = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        destination_section_uid=owner_person.getUid(),
        simulation_state="started"
      )
      self.assertEqual(payment_transaction.getSpecialiseValue().getTradeConditionType(), "deposit")
      # payzen/wechat or accountant will only stop the payment
      payment_transaction.stop()
      self.tic()
      assert payment_transaction.receivable.getGroupingReference(None) is not None
      self.login(owner_person.getUserId())

      amount = sum([i.total_price for i in owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())])
      self.assertEqual(0, amount)

    ##################################################
    # Add first batch of service, and generate invoices
    with PinnedDateTime(self, creation_date):
      self.logout()
      self.login(owner_person.getUserId())
      self.portal.portal_slap.requestComputer(self.generateNewId(),
                                              project.getReference())
      self.portal.portal_slap.requestComputerPartition(
        software_release=software_release_url,
        software_type=software_type,
        partition_reference=self.generateNewId(),
        shared_xml='<marshal><bool>0</bool></marshal>',
        project_reference=project.getReference())

      self.logout()
      self.login()
      # Execute activities for all services
      # To try detection bad activity tag dependencies
      self.tic()

      # Get object
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type='Instance Tree',
        follow_up__uid=project.getUid()
      )
      compute_node = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node',
        follow_up__uid=project.getUid()
      )

    return project, owner_person, instance_tree, compute_node

  def test_notPaidInvoiceScenario(self):
    """
    Ensure services are destroyed, open order are archived, and
    deposit is used to pay the invoice
    """
    creation_date = DateTime('2024/05/19')
    project, owner_person, instance_tree, compute_node = self.bootstrapCRMScenario(
      creation_date)

    ##################################################
    # Ensure new monthly invoices are created
    # Regularisation Request must also be created
    with PinnedDateTime(self, creation_date + 32):
      self.logout()
      self.login()
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()
      regularisation_request = self.portal.portal_catalog.getResultValue(
        portal_type='Regularisation Request',
        simulation_state='suspended',
        destination__uid=owner_person.getUid()
      )
      self.assertNotEqual(regularisation_request, None)
      self.assertEqual(regularisation_request.getSimulationState(), 'suspended')

    ##################################################
    # Trigger regularisation request escalation
    self.logout()
    self.login()
    for date_offset in range(33, 70, 1):
      # Trigger the alarm everyday, to not depend too much
      # of the alarm crm delay current implementation
      with PinnedDateTime(self, creation_date + date_offset):
        for alarm_id in [
          'slapos_crm_trigger_acknowledgment_escalation',
          'slapos_crm_trigger_delete_reminder_escalation',
          'update_open_order_simulation',
          'slapos_stop_confirmed_aggregated_sale_invoice_transaction'
        ]:
          self.portal.portal_alarms[alarm_id].activeSense()
        self.tic()

    ##################################################
    # Items must be deleted
    # Open Order must be archived
    # Invoice must be paid with Deposit
    self.assertEqual(project.getValidationState(), 'invalidated')
    self.assertEqual(instance_tree.getValidationState(), 'archived')
    self.assertEqual(instance_tree.getSlapState(), 'destroy_requested')
    self.assertEqual(compute_node.getValidationState(), 'invalidated')
    open_order_list = self.portal.portal_catalog(
      portal_type='Open Sale Order',
      destination_section__uid=owner_person.getUid()
    )
    hosting_subscription_list = []
    self.assertEqual(len(open_order_list), 3)
    for open_order in open_order_list:
      self.assertEqual(open_order.getValidationState(), 'archived')
      self.assertNotEqual(open_order.getStopDate(), open_order.getStartDate())
      self.assertNotEqual(open_order.getStopDate(), None)
      self.assertEqual(open_order.getStopDate(), DateTime('2024/07/17'))

      for line in open_order.contentValues():
        for cell in line.contentValues():
          hosting_subscription_list.append(
            cell.getAggregateValue(portal_type='Hosting Subscription')
          )
        tmp = line.getAggregateValue(portal_type='Hosting Subscription')
        if tmp is not None:
          hosting_subscription_list.append(tmp)

    self.assertEqual(len(hosting_subscription_list), 3)
    for hosting_subscription in hosting_subscription_list:
      self.assertEqual(hosting_subscription.getValidationState(), 'archived')

    self.assertEqual(regularisation_request.getSimulationState(), 'suspended')
    self.assertEqual(regularisation_request.getResourceId(),
                      'slapos_crm_delete_acknowledgement')

    # No planned invoice is expected
    ledger_uid = self.portal.portal_categories.ledger.automated.getUid()
    outstanding_amount_list = owner_person.Entity_getOutstandingAmountList(
      ledger_uid=ledger_uid
    )
    self.assertEqual(len(outstanding_amount_list), 1)
    self.assertEqual(outstanding_amount_list[0].total_price, 132)

    planned_outstanding_amount_list = owner_person.Entity_getOutstandingAmountList(
      ledger_uid=ledger_uid,
      include_planned=True
    )
    self.assertEqual(len(planned_outstanding_amount_list), 1)
    self.assertEqual(outstanding_amount_list[0].total_price,
                      planned_outstanding_amount_list[0].total_price)


    with PinnedDateTime(self, creation_date + 5):
      self.checkERP5StateBeforeExit()


  def test_notPaidInvoiceScenario_open_regularisation_request(self):
    """
    Ensure services are destroyed, open order are archived, and
    deposit is used to pay the invoice
    """
    creation_date = DateTime('2024/05/19')
    project, owner_person, instance_tree, compute_node = self.bootstrapCRMScenario(
      creation_date)

    ##################################################
    # Ensure new monthly invoices are created
    # Regularisation Request must also be created
    with PinnedDateTime(self, creation_date + 32):
      self.logout()
      self.login()
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()
      regularisation_request = self.portal.portal_catalog.getResultValue(
        portal_type='Regularisation Request',
        simulation_state='suspended',
        destination__uid=owner_person.getUid()
      )
      self.assertNotEqual(regularisation_request, None)
      self.assertEqual(regularisation_request.getSimulationState(), 'suspended')


    with PinnedDateTime(self, creation_date + 32.1):
      self.login(owner_person.getUserId())
      # Ensure that posting a ticket dont re-open the ticket.
      event = regularisation_request.Ticket_createProjectEvent(
        'foo', 'incoming', 'Web Message',
        regularisation_request.getResource(),
        'bar', "text/plain"
      )
      self.tic()
      self.assertEqual(regularisation_request.getSimulationState(), 'suspended')
      self.assertEqual(event.getSimulationState(), 'stopped')

    self.logout()
    self.login()
    regularisation_request.validate()

    ##################################################
    # Trigger regularisation request escalation
    self.logout()
    self.login()
    for date_offset in range(33, 70, 1):
      # Trigger the alarm everyday, to not depend too much
      # of the alarm crm delay current implementation
      with PinnedDateTime(self, creation_date + date_offset):
        for alarm_id in [
          'slapos_crm_trigger_acknowledgment_escalation',
          'slapos_crm_trigger_delete_reminder_escalation',
          'update_open_order_simulation',
          'slapos_stop_confirmed_aggregated_sale_invoice_transaction'
        ]:
          self.portal.portal_alarms[alarm_id].activeSense()
        self.tic()

    ##################################################
    # All items are preserved nothing happened
    self.assertEqual(project.getValidationState(), 'validated')
    self.assertEqual(instance_tree.getValidationState(), 'validated')
    self.assertEqual(instance_tree.getSlapState(), 'start_requested')
    self.assertEqual(compute_node.getValidationState(), 'validated')
    open_order_list = self.portal.portal_catalog(
      portal_type='Open Sale Order',
      destination_section__uid=owner_person.getUid()
    )
    self.assertEqual(len(open_order_list), 3)
    for open_order in open_order_list:
      self.assertEqual(open_order.getValidationState(), 'validated')

    self.assertEqual(regularisation_request.getSimulationState(), 'validated')
    self.assertEqual(regularisation_request.getResourceId(),
                      'slapos_crm_acknowledgement')

    with PinnedDateTime(self, creation_date + 5):
      self.checkERP5StateBeforeExit()
