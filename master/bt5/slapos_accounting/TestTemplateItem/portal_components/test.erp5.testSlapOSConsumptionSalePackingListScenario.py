# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2018 Nexedi SA and Contributors. All Rights Reserved.
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

from erp5.component.test.SlapOSTestCaseMixin import \
    PinnedDateTime
from erp5.component.test.testSlapOSERP5VirtualMasterScenario import \
    TestSlapOSVirtualMasterScenarioMixin
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
import pkg_resources
from Products.ERP5Type.Utils import str2bytes


MAIN_TRADE_CONDITION_CREATION_DATE = DateTime('2026/03/29 03:04')


class TestSlapOSLinkConsumptionToCustomerAlarm(TestSlapOSVirtualMasterScenarioMixin):

  def bootstrapComsumptionTest(
    self,
    currency_creation_date=MAIN_TRADE_CONDITION_CREATION_DATE,
    is_virtual_master_accountable=False,
    new_document_day_delay_count=0,
    manager_count=0,
    manager_project_count=0,
    project_node_count=0,
    project_customer_count=0,
    customer_instance_count=1,
  ):

    result_dict = {
      'manager_list': [],
      'customer_list': [],
    }

    current_zope_date = currency_creation_date
    with PinnedDateTime(self, current_zope_date):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(
        is_virtual_master_accountable=is_virtual_master_accountable
      )
      # Tic to ensure sale supply are indexed too before creating the project
      self.tic()

    for manager_index in range(manager_count):
      current_zope_date = addToDate(current_zope_date, to_add={'day': new_document_day_delay_count})
      with PinnedDateTime(self, current_zope_date):
        # lets join as slapos administrator, which will own few compute_nodes
        owner_reference = 'owner-%i-%s' % (manager_index, self.generateNewId())
        owner_person = self.joinSlapOS(owner_reference)
        result_dict['manager_list'].append(owner_person)

        ##################################################
        # Add deposit
        if is_virtual_master_accountable:
          # Just add some large sum, so instances dont get blocked.
          tmp_subscription_request = self.portal.portal_trash.newContent(
            portal_type='Subscription Request',
            temp_object=True,
            start_date=DateTime(),
            # source_section rely on default trade condition, like the rest.
            destination_value=owner_person,
            destination_section_value=owner_person,
            ledger_value=self.portal.portal_categories.ledger.automated,
            price_currency=currency.getRelativeUrl(),
            total_price=99 * 10
          )

          payment_transaction = owner_person.Entity_createDepositPaymentTransaction(
            [tmp_subscription_request])
          # payzen interface will only stop the payment
          payment_transaction.stop()
          self.tic()

      for project_index in range(manager_project_count):

        # hooray, now it is time to create compute_nodes
        self.login(sale_person.getUserId())

        current_zope_date = addToDate(current_zope_date, to_add={'day': new_document_day_delay_count})
        with PinnedDateTime(self, current_zope_date):
          # create a default project
          project = self.portal.restrictedTraverse(self.addProject(
            person=owner_person,
            currency=currency,
            is_accountable=False
          ))
          self.tic()

        self.login(owner_person.getUserId())
        if customer_instance_count:
          software_product = self._makeSoftwareProduct(project)
          release_variation = software_product.contentValues(portal_type='Software Product Release Variation')[0]
          type_variation = software_product.contentValues(portal_type='Software Product Type Variation')[0]

        project_compute_node_list = []
        for project_node_index in range(project_node_count):
          current_zope_date = addToDate(current_zope_date, to_add={'day': new_document_day_delay_count})
          with PinnedDateTime(self, current_zope_date):
            public_server_title = 'Public Server %s for %s' % (project_node_index + 1, owner_reference)
            project_compute_node_list.append(self.requestComputeNode(public_server_title, project.getReference()))
            self.tic()

        if customer_instance_count:
          software_product = self._makeSoftwareProduct(project)
          release_variation = software_product.contentValues(portal_type='Software Product Release Variation')[0]
          type_variation = software_product.contentValues(portal_type='Software Product Type Variation')[0]

          for project_node in project_compute_node_list:
            self.addAllocationSupply("for compute node %s" % project_node, project_node, software_product,
                                       release_variation, type_variation)
            # and install some software on them
            self.supplySoftware(project_node, release_variation.getUrlString())
            # format the compute_nodes
            self.formatComputeNode(project_node)
          self.tic()

          for project_customer_index in range(project_customer_count):
            current_zope_date = addToDate(current_zope_date, to_add={'day': new_document_day_delay_count})
            with PinnedDateTime(self, current_zope_date):
              # lets join as slapos administrator, which will own few compute_nodes
              customer_reference = 'customer-%i-%i-%i-%s' % (manager_index, project_index, project_customer_index, self.generateNewId())
              customer_person = self.joinSlapOS(customer_reference)
              result_dict['customer_list'].append(customer_person)

            for customer_instance_index in range(customer_instance_count):
              current_zope_date = addToDate(current_zope_date, to_add={'day': new_document_day_delay_count})
              with PinnedDateTime(self, current_zope_date):
                request_kw = dict(
                  software_release=release_variation.getUrlString(),
                  software_type=type_variation.getTitle(),
                  instance_xml=self.generateSafeXml(),
                  sla_xml=self.generateEmptyXml(),
                  shared=False,
                  software_title='test tree %i %i %i' % (manager_index, project_index, customer_instance_index),
                  state='started',
                  project_reference=project.getReference()
                )
                customer_person.requestSoftwareInstance(**request_kw)
                self.tic()
    return result_dict

  #################################################################
  # slapos_accounting_link_consumption_to_customer
  #################################################################
  def test_createSPLAggregateByManager(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=False,
      new_document_day_delay_count=1,
      manager_count=2,
      manager_project_count=1,
      project_node_count=1,
      project_customer_count=0,
      customer_instance_count=0,
    )

    manager_person = user_dict['manager_list'][0]
    self.login()

    # Ensure no unexpected object has been created
    # 3 assignment request
    # 1 credential request
    # 1 event
    # 2 open sale order / line
    # 1 simulation movement
    # 1 project
    # 2 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(manager_person, 12)
    previous_sale_packing_list_uid_list = [x.getUid() for x in self.portal.portal_catalog(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid()
    )]

    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/04/27')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    self.assertRelatedObjectCount(manager_person, 13)
    aggregated_sale_packinglist = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid(),
      uid=NegatedQuery(SimpleQuery(uid=previous_sale_packing_list_uid_list)),
    )
    self.assertEqual(aggregated_sale_packinglist.getPortalType(), "Sale Packing List")
    self.assertEqual(aggregated_sale_packinglist.getSourceSection(), None)
    self.assertEqual(aggregated_sale_packinglist.getSourceValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getDestination(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationDecision(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationSection(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getStartDate(), DateTime('2026/03/28 00:00:00 UTC'))
    self.assertEqual(aggregated_sale_packinglist.getStopDate(), DateTime('2026/04/28 00:00:00 UTC'))
    self.assertTrue(aggregated_sale_packinglist.getReference(), aggregated_sale_packinglist.getReference())
    self.assertEqual(aggregated_sale_packinglist.getSimulationState(), "delivered")
    self.assertEqual(aggregated_sale_packinglist.getCausalityState(), "solved")
    self.assertEqual(aggregated_sale_packinglist.getSpecialiseValue().getPortalType(), 'Sale Trade Condition')
    self.assertEqual(aggregated_sale_packinglist.getSourceProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getDestinationProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getLedger(), 'automated')
    self.assertEqual(aggregated_sale_packinglist.getPriceCurrencyValue().getPortalType(), 'Currency')

    self.assertEqual(len(aggregated_sale_packinglist.contentIds()), 1)
    sale_packing_list_line = aggregated_sale_packinglist.contentValues()[0]
    self.assertEqual(sale_packing_list_line.getResource(), 'service_module/slapos_compute_node_subscription')
    self.assertEqual(sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(sale_packing_list_line.getPrice(), 0)
    self.assertEqual(sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    # check matching internal packing list line
    self.assertEqual(self.portal.portal_catalog.countResults(
      portal_type='Internal Packing List Line',
      grouping_reference=sale_packing_list_line.getGroupingReference()
    )[0][0], 1)
    self.assertEqual(len(aggregated_sale_packinglist.getCausalityList()), 1)

  def test_createSPLGatherAllManagerProjects(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=False,
      new_document_day_delay_count=1,
      manager_count=1,
      manager_project_count=2,
      project_node_count=1,
      project_customer_count=1,
      customer_instance_count=2,
    )

    manager_person = user_dict['manager_list'][0]
    self.login()

    # Ensure no unexpected object has been created
    # 5 assignment request
    # 1 credential request
    # 1 event
    # 4 open sale order / line
    # 2 simulation movement
    # 2 project
    # 4 sale packing list
    # 2 subscription request
    self.assertRelatedObjectCount(manager_person, 21)
    previous_sale_packing_list_uid_list = [x.getUid() for x in self.portal.portal_catalog(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid()
    )]

    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/04/27')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    self.assertRelatedObjectCount(manager_person, 22)
    aggregated_sale_packinglist = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid(),
      uid=NegatedQuery(SimpleQuery(uid=previous_sale_packing_list_uid_list)),
    )
    self.assertEqual(aggregated_sale_packinglist.getPortalType(), "Sale Packing List")
    self.assertEqual(aggregated_sale_packinglist.getSourceSection(), None)
    self.assertEqual(aggregated_sale_packinglist.getSourceValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getDestination(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationDecision(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationSection(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getStartDate(), DateTime('2026/03/28 00:00:00 UTC'))
    self.assertEqual(aggregated_sale_packinglist.getStopDate(), DateTime('2026/04/28 00:00:00 UTC'))
    self.assertTrue(aggregated_sale_packinglist.getReference(), aggregated_sale_packinglist.getReference())
    self.assertEqual(aggregated_sale_packinglist.getSimulationState(), "delivered")
    self.assertEqual(aggregated_sale_packinglist.getCausalityState(), "solved")
    self.assertEqual(aggregated_sale_packinglist.getSpecialiseValue().getPortalType(), 'Sale Trade Condition')
    self.assertEqual(aggregated_sale_packinglist.getSourceProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getDestinationProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getLedger(), 'automated')
    self.assertEqual(aggregated_sale_packinglist.getPriceCurrencyValue().getPortalType(), 'Currency')

    self.assertEqual(len(aggregated_sale_packinglist.contentIds()), 2)
    sale_packing_list_line_list = aggregated_sale_packinglist.contentValues()

    node_sale_packing_list_line = [x for x in sale_packing_list_line_list if x.getResource() == 'service_module/slapos_compute_node_subscription'][0]
    self.assertEqual(node_sale_packing_list_line.getResource(), 'service_module/slapos_compute_node_subscription')
    self.assertEqual(node_sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(node_sale_packing_list_line.getQuantity(), 2)
    self.assertEqual(node_sale_packing_list_line.getPrice(), 0)
    self.assertEqual(node_sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    instance_sale_packing_list_line = [x for x in sale_packing_list_line_list if x.getResource() == 'service_module/slapos_software_instance_subscription'][0]
    self.assertEqual(instance_sale_packing_list_line.getResource(), 'service_module/slapos_software_instance_subscription')
    self.assertEqual(instance_sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(instance_sale_packing_list_line.getQuantity(), 4)
    self.assertEqual(instance_sale_packing_list_line.getPrice(), 0)
    self.assertEqual(instance_sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    # check matching internal packing list line
    self.assertEqual(self.portal.portal_catalog.countResults(
      portal_type='Internal Packing List Line',
      grouping_reference=aggregated_sale_packinglist.getReference()
    )[0][0], 6)
    self.assertEqual(len(aggregated_sale_packinglist.getCausalityList()), 6)

  def test_createSPLOneDayBeforeEndOfPeriod(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=False,
      new_document_day_delay_count=1,
      manager_count=1,
      manager_project_count=1,
      project_customer_count=1,
      customer_instance_count=1,
    )

    manager_person = user_dict['manager_list'][0]

    # Ensure no unexpected object has been created
    # 3 assignment request
    # 1 credential request
    # 1 event
    # 2 open sale order / line
    # 1 simulation movement
    # 1 project
    # 2 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(manager_person, 12)

    with PinnedDateTime(self, DateTime('2026/04/26')):
      alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
      alarm.activeSense()
      self.tic()
    self.assertRelatedObjectCount(manager_person, 12)

    with PinnedDateTime(self, DateTime('2026/04/28')):
      alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
      alarm.activeSense()
      self.tic()
    self.assertRelatedObjectCount(manager_person, 12)

    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/04/27')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    # 3 assignment request
    # 1 credential request
    # 1 event
    # 2 open sale order / line
    # 1 simulation movement
    # 1 project
    # 3 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(manager_person, 13)

  def test_createSPLWithAccounting(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=True,
      new_document_day_delay_count=1,
      manager_count=1,
      manager_project_count=1,
      project_node_count=1,
      project_customer_count=1,
      customer_instance_count=1,
    )

    manager_person = user_dict['manager_list'][0]
    self.login()

    # Ensure no unexpected object has been created
    # 4 accounting transactions
    # 3 assignment request
    # 1 credential request
    # 2 event
    # 2 open sale order / line
    # 18 simulation movement
    # 1 project
    # 1 regularisation request
    # 3 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(manager_person, 36)
    previous_sale_packing_list_uid_list = [x.getUid() for x in self.portal.portal_catalog(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid()
    )]

    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/04/27')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    # and many simulation movements
    self.assertRelatedObjectCount(manager_person, 51)
    aggregated_sale_packinglist = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List',
      destination__uid=manager_person.getUid(),
      uid=NegatedQuery(SimpleQuery(uid=previous_sale_packing_list_uid_list)),
    )
    self.assertEqual(aggregated_sale_packinglist.getPortalType(), "Sale Packing List")
    self.assertEqual(aggregated_sale_packinglist.getSourceSectionValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getSourceValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getDestination(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationDecision(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationSection(), manager_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getStartDate(), DateTime('2026/03/28 00:00:00 UTC'))
    self.assertEqual(aggregated_sale_packinglist.getStopDate(), DateTime('2026/04/28 00:00:00 UTC'))
    self.assertTrue(aggregated_sale_packinglist.getReference(), aggregated_sale_packinglist.getReference())
    self.assertEqual(aggregated_sale_packinglist.getSimulationState(), "delivered")
    self.assertEqual(aggregated_sale_packinglist.getCausalityState(), "solved")
    self.assertEqual(aggregated_sale_packinglist.getSpecialiseValue().getPortalType(), 'Sale Trade Condition')
    self.assertEqual(aggregated_sale_packinglist.getSourceProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getDestinationProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getLedger(), 'automated')
    self.assertEqual(aggregated_sale_packinglist.getPriceCurrencyValue().getPortalType(), 'Currency')

    self.assertEqual(len(aggregated_sale_packinglist.contentIds()), 2)
    sale_packing_list_line_list = aggregated_sale_packinglist.contentValues()

    node_sale_packing_list_line = [x for x in sale_packing_list_line_list if x.getResource() == 'service_module/slapos_compute_node_subscription'][0]
    self.assertEqual(node_sale_packing_list_line.getResource(), 'service_module/slapos_compute_node_subscription')
    self.assertEqual(node_sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(node_sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(node_sale_packing_list_line.getPrice(), 2)
    self.assertEqual(node_sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    instance_sale_packing_list_line = [x for x in sale_packing_list_line_list if x.getResource() == 'service_module/slapos_software_instance_subscription'][0]
    self.assertEqual(instance_sale_packing_list_line.getResource(), 'service_module/slapos_software_instance_subscription')
    self.assertEqual(instance_sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(instance_sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(instance_sale_packing_list_line.getPrice(), 1)
    self.assertEqual(instance_sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    # check matching internal packing list line
    self.assertEqual(self.portal.portal_catalog.countResults(
      portal_type='Internal Packing List Line',
      grouping_reference=aggregated_sale_packinglist.getReference()
    )[0][0], 2)
    self.assertEqual(len(aggregated_sale_packinglist.getCausalityList()), 2)

    # check that the invoice has all the lines
    # 2 for the project subscription (discount and expected subscription)
    # 1 for taxes
    # 2 for node and instance consumptions
    ongoing_invoice = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Invoice Transaction',
      destination_section__uid=manager_person.getUid(),
      simulation_state='confirmed'
    )
    self.assertAlmostEqual(ongoing_invoice.getTotalPrice(), 48.96)
    # 3 sale packing list (discount, open order and consumption)
    self.assertEqual(len(ongoing_invoice.getCausalityList()), 3)
    self.assertEqual(len(ongoing_invoice.contentValues(portal_type='Invoice Line')), 5)

  #################################################################
  # slapos_accounting_link_consumption_to_customer
  # tioxml
  #################################################################
  def test_createSPLAggregateByCustomer(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=False,
      new_document_day_delay_count=1,
      manager_count=1,
      manager_project_count=1,
      project_node_count=1,
      project_customer_count=1,
      customer_instance_count=1,
    )

    customer_person = user_dict['customer_list'][0]
    self.login()

    # Ensure no unexpected object has been created
    # 1 assignment request
    # 1 credential request
    # 1 event
    # 1 instance tree
    # 3 open sale order / line
    # 1 simulation movement
    # 2 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(customer_person, 11)
    """
    previous_sale_packing_list_uid_list = [x.getUid() for x in self.portal.portal_catalog(
      portal_type='Sale Packing List',
      destination__uid=customer_person.getUid()
    )]
"""
    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/05/01')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    self.assertRelatedObjectCount(customer_person, 11)
    """
    aggregated_sale_packinglist = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List',
      destination__uid=customer_person.getUid(),
      uid=NegatedQuery(SimpleQuery(uid=previous_sale_packing_list_uid_list)),
    )
    self.assertEqual(aggregated_sale_packinglist.getPortalType(), "Sale Packing List")
    self.assertEqual(aggregated_sale_packinglist.getSourceSection(), None)
    self.assertEqual(aggregated_sale_packinglist.getSourceValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getDestination(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationDecision(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationSection(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getStartDate(), DateTime('2026/03/28 00:00:00 UTC'))
    self.assertEqual(aggregated_sale_packinglist.getStopDate(), DateTime('2026/04/28 00:00:00 UTC'))
    self.assertTrue(aggregated_sale_packinglist.getReference(), aggregated_sale_packinglist.getReference())
    self.assertEqual(aggregated_sale_packinglist.getSimulationState(), "delivered")
    self.assertEqual(aggregated_sale_packinglist.getCausalityState(), "solved")
    self.assertEqual(aggregated_sale_packinglist.getSpecialiseValue().getPortalType(), 'Sale Trade Condition')
    self.assertEqual(aggregated_sale_packinglist.getSourceProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getDestinationProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getLedger(), 'automated')
    self.assertEqual(aggregated_sale_packinglist.getPriceCurrencyValue().getPortalType(), 'Currency')

    self.assertEqual(len(aggregated_sale_packinglist.contentIds()), 1)
    sale_packing_list_line = aggregated_sale_packinglist.contentValues()[0]
    self.assertEqual(sale_packing_list_line.getResource(), 'service_module/slapos_compute_node_subscription')
    self.assertEqual(sale_packing_list_line.getQuantityUnit(), 'time/month')
    self.assertEqual(sale_packing_list_line.getQuantity(), 1)
    self.assertEqual(sale_packing_list_line.getPrice(), 0)
    self.assertEqual(sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    # check matching internal packing list line
    self.assertEqual(self.portal.portal_catalog.countResults(
      portal_type='Internal Packing List Line',
      grouping_reference=sale_packing_list_line.getGroupingReference()
    )[0][0], 1)
"""

  def test_createSPLTioXML(self):
    user_dict = self.bootstrapComsumptionTest(
      DateTime(MAIN_TRADE_CONDITION_CREATION_DATE),
      is_virtual_master_accountable=False,
      new_document_day_delay_count=1,
      manager_count=1,
      manager_project_count=1,
      project_node_count=1,
      project_customer_count=1,
      customer_instance_count=1,
    )

    # manager_person = user_dict['manager_list'][0]
    customer_person = user_dict['customer_list'][0]
    self.login()

    # Ensure no unexpected object has been created
    # 1 assignment request
    # 1 credential request
    # 1 event
    # 1 instance tree
    # 3 open sale order / line
    # 1 simulation movement
    # 2 sale packing list
    # 1 subscription request
    self.assertRelatedObjectCount(customer_person, 11)
    previous_sale_packing_list_uid_list = [x.getUid() for x in self.portal.portal_catalog(
      portal_type='Sale Packing List',
      destination__uid=customer_person.getUid()
    )]

    instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=customer_person.getUid(),
    )
    software_instance = instance_tree.getSuccessorValue()
    public_server = self.portal.portal_catalog.getResultValue(
      portal_type='Compute Node',
      follow_up__uid=instance_tree.getFollowUpUid(),
    )

    consumption_service = self.addConsumptionService()
    self.addConsumptionSupply("For compute node", public_server, consumption_service)
    self.tic()
    # Minimazed version of the original file, only with a sub-set of values
    # that matter
    consumption_xml_report = """<?xml version="1.0" encoding="utf-8"?>
<journal>
<transaction type="Sale Packing List">
  <title>Test Consumption file for %(compute_node_reference)s </title>
  <start_date>2026-04-14 00:00:00</start_date>
  <stop_date>2026-04-17 23:59:59</stop_date>
  <reference>2026-04-17-global</reference>
  <currency/>
  <payment_mode/>
  <category/>
  <arrow type="Destination"/>
  <movement>
    <resource>%(service_reference)s</resource>
    <title>%(service_title)s</title>
    <reference>%(software_instance_reference)s</reference>
    <quantity>29.12</quantity>
    <price>0.0</price>
    <VAT/>
    <category/>
  </movement>
</transaction>
</journal>""" % ({
      'software_instance_reference': software_instance.getReference(),
      'compute_node_reference': public_server.getReference(),
      'service_reference': consumption_service.getReference(),
      'service_title': consumption_service.getTitle()})

    compute_node_consumption_model = \
      pkg_resources.resource_string(
        'slapos.slap',
        'doc/computer_consumption.xsd')

    # Ensure what is written above is valid
    self.assertTrue(self.portal.portal_slap._validateXML(
      str2bytes(consumption_xml_report), compute_node_consumption_model))

    # Simulate computer upload
    response = self.portal.portal_slap.useComputer(
       public_server.getReference(), consumption_xml_report)
    # Ensure it succeed
    self.assertEqual(200, response.status)
    self.assertEqual(b"OK", response.body)
    self.tic()

    # This valid date is the manager creation date (max 28) minus 1
    with PinnedDateTime(self, DateTime('2026/05/01')):
      for _ in range(2):
        # Run twice, to ensure packing list have a grouping reference
        alarm = self.portal.portal_alarms.slapos_accounting_link_consumption_to_customer
        alarm.activeSense()
        self.tic()

    # one new sale packing list created
    self.assertRelatedObjectCount(customer_person, 12)
    aggregated_sale_packinglist = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Packing List',
      destination__uid=customer_person.getUid(),
      uid=NegatedQuery(SimpleQuery(uid=previous_sale_packing_list_uid_list)),
    )
    self.assertEqual(aggregated_sale_packinglist.getPortalType(), "Sale Packing List")
    self.assertEqual(aggregated_sale_packinglist.getSourceSection(), None)
    self.assertEqual(aggregated_sale_packinglist.getSourceValue().getPortalType(), "Organisation")
    self.assertEqual(aggregated_sale_packinglist.getDestination(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationDecision(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getDestinationSection(), customer_person.getRelativeUrl())
    self.assertEqual(aggregated_sale_packinglist.getStartDate(), DateTime('2026/04/02 00:00:00 UTC'))
    self.assertEqual(aggregated_sale_packinglist.getStopDate(), DateTime('2026/05/02 00:00:00 UTC'))
    self.assertTrue(aggregated_sale_packinglist.getReference(), aggregated_sale_packinglist.getReference())
    self.assertEqual(aggregated_sale_packinglist.getSimulationState(), "delivered")
    self.assertEqual(aggregated_sale_packinglist.getCausalityState(), "solved")
    self.assertEqual(aggregated_sale_packinglist.getSpecialiseValue().getPortalType(), 'Sale Trade Condition')
    self.assertEqual(aggregated_sale_packinglist.getSourceProject(), public_server.getFollowUp())
    self.assertEqual(aggregated_sale_packinglist.getDestinationProject(), None)
    self.assertEqual(aggregated_sale_packinglist.getLedger(), 'automated')
    self.assertEqual(aggregated_sale_packinglist.getPriceCurrencyValue().getPortalType(), 'Currency')

    self.assertEqual(len(aggregated_sale_packinglist.contentIds()), 1)
    sale_packing_list_line = aggregated_sale_packinglist.contentValues()[0]
    self.assertEqual(sale_packing_list_line.getResource(), consumption_service.getRelativeUrl())
    self.assertEqual(sale_packing_list_line.getQuantityUnit(), 'unit/piece')
    self.assertAlmostEqual(sale_packing_list_line.getQuantity(), 29.12)
    self.assertEqual(sale_packing_list_line.getPrice(), 0)
    self.assertEqual(sale_packing_list_line.getGroupingReference(), aggregated_sale_packinglist.getReference())

    # check matching internal packing list line
    self.assertEqual(self.portal.portal_catalog.countResults(
      portal_type='Internal Packing List Line',
      grouping_reference=sale_packing_list_line.getGroupingReference()
    )[0][0], 1)
    self.assertEqual(len(aggregated_sale_packinglist.getCausalityList()), 1)

