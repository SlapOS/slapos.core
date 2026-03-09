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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, \
  TemporaryAlarmScript, Simulator, simulate, PinnedDateTime
from unittest import expectedFailure
from zExceptions import Unauthorized

import os
import tempfile
from DateTime import DateTime


class TestSlapOSOpenInternalOrderCreationAlarm(SlapOSTestCaseMixin):

  #################################################################
  # slapos_subscription_request_create_from_orphaned_item
  #################################################################
  def _test_slapos_open_internal_order_create_from_orphaned_item(self, portal_type):
    script_name = "Item_createOpenInternalOrder"
    alarm = self.portal.portal_alarms.slapos_open_internal_order_create_from_orphaned_item

    #####################################################
    # Instance Tree without Open Internal Order
    document = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    self._test_alarm(alarm, document, script_name)

    #####################################################
    # Instance Tree with Subscription Request
    document = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    open_order = self.portal.open_internal_order_module.newContent(
      portal_type='Open Internal Order',
      title="Test Subscription Request %s" % self.new_id,
    )
    open_order.newContent(
      portal_type='Open Internal Order Line',
      aggregate_value=document
    )
    self.tic()
    self._test_alarm_not_visited(alarm, document, script_name)
    #####################################################
    # Instance Tree aggregated to another portal type
    document = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title="Test %s another portal type %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    self.portal.sale_packing_list_module.newContent(
      portal_type='Sale Packing List',
      title="Test Sale Packing List %s" % self.new_id,
    ).newContent(
      portal_type="Sale Packing List Line",
      aggregate_value=document
    )
    self.tic()
    self._test_alarm(alarm, document, script_name)

  def test_Item_createOpenInternalOrder_alarm_fromOrphanedInstanceTree(self):
    portal_type = 'Instance Tree'
    script_name = "Item_createOpenInternalOrder"
    alarm = self.portal.portal_alarms.slapos_open_internal_order_create_from_orphaned_item
    document = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    self._test_alarm_not_visited(alarm, document, script_name)

  def test_Item_createOpenInternalOrder_alarm_fromOrphanedProject(self):
    portal_type = 'Project'
    script_name = "Item_createOpenInternalOrder"
    alarm = self.portal.portal_alarms.slapos_open_internal_order_create_from_orphaned_item
    document = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
      title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    self._test_alarm_not_visited(alarm, document, script_name)

  def test_Item_createOpenInternalOrder_alarm_fromOrphanedSoftwareInstance(self):
    self._test_slapos_open_internal_order_create_from_orphaned_item("Software Instance")

  def test_Item_createOpenInternalOrder_alarm_fromOrphanedSlaveInstance(self):
    self._test_slapos_open_internal_order_create_from_orphaned_item("Slave Instance")

  def test_Item_createOpenInternalOrder_alarm_fromOrphanedComputeNode(self):
    self._test_slapos_open_internal_order_create_from_orphaned_item("Compute Node")

  def test_Item_createOpenInternalOrder_script_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Item_createOpenInternalOrder,
      REQUEST={}
    )

  def test_Item_createOpenInternalOrder_script_fromOrphanedComputeNode(self):
    _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(
      allocation_state='impossible'
    )
    project = instance_tree.getFollowUpValue()

    with self.changeContextByDisablingPortalAlarm():
      with PinnedDateTime(self, DateTime('2023/05/19')):
        document, _ = self.addComputeNodeAndPartition(project=project)
      with PinnedDateTime(self, DateTime('2026/03/22')):
        self.tic()

    open_sale_order = self.portal.portal_catalog.getResultValue(
      portal_type=['Open Sale Order Line'],
      aggregate__uid=project.getUid(),
      validation_state='validated',
    ).getParentValue()

    with PinnedDateTime(self, DateTime('2026/03/25')):
      open_order = document.Item_createOpenInternalOrder()
    self.assertNotEqual(open_order, None)

    self.assertEqual(open_order.getValidationState(), 'validated')
    self.assertEqual(
      open_order.getStartDate(),
      DateTime('2026/03/19 00:00:00 UTC')
    )
    self.assertEqual(open_order.getStopDate(), open_order.getStartDate())
    self.assertEqual(
      open_order.getSpecialise(),
      'business_process_module/slapos_internal_subscription_business_process'
    )
    self.assertEqual(
      open_order.getDestination(-1),
      open_sale_order.getSource(-2)
    )
    self.assertEqual(open_order.getDestinationSection(), None)
    self.assertEqual(open_order.getSourceSection(), None)
    self.assertEqual(open_order.getSource(), None)
    self.assertEqual(open_order.getLedger(), 'automated')

    open_order_line = open_order.contentValues(
      portal_type="Open Internal Order Line",
    )[0]
    self.assertEqual(
      open_order_line.getResource(),
      'service_module/slapos_compute_node_subscription'
    )
    self.assertEqual(open_order_line.getQuantity(), 1)
    self.assertEqual(open_order_line.getPrice(), 0)
    self.assertTrue(
      open_order_line.isMemberOf('aggregate/%s' % document.getRelativeUrl())
    )

    consumption_subscription = open_order_line.getAggregateValue(
      portal_type='Consumption Subscription'
    )
    self.assertEqual(consumption_subscription.getLedger(), 'automated')
    self.assertSameSet(consumption_subscription.getPeriodicityHourList(), [0])
    self.assertSameSet(consumption_subscription.getPeriodicityMinuteList(), [0])
    self.assertSameSet(consumption_subscription.getPeriodicityMonthDayList(), [19])


class TestSlapOSTriggerBuildAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_trigger_build
  #################################################################
  def test_SimulationMovement_buildSlapOS_alarm_withoutDelivery(self):
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        ledger='automated',
        title='Not visited by SimulationMovement_buildSlapOS')
    with TemporaryAlarmScript(self.portal, 'SimulationMovement_buildSlapOS', "''", attribute='title'):
      self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_trigger_build,
      simulation_movement,
      'SimulationMovement_buildSlapOS',
      attribute='title'
    )

  def test_SimulationMovement_buildSlapOS_alarm_withDelivery(self):
    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        ledger='automated',
        delivery=delivery_line.getRelativeUrl(),
        title='Not visited by SimulationMovement_buildSlapOS')
    with TemporaryAlarmScript(self.portal, 'SimulationMovement_buildSlapOS', "''", attribute='title'):
      self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_trigger_build,
      simulation_movement,
      'SimulationMovement_buildSlapOS',
      attribute='title'
    )

  #################################################################
  # SimulationMovement_buildSlapOS
  #################################################################
  def test_SimulationMovement_buildSlapOS_script_withoutDelivery(self):
    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]

    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality_value=root_business_link,
        specialise_value=business_process,
        ledger='automated',
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality_value=business_link,
        specialise_value=business_process,
        ledger='automated',
        portal_type='Simulation Movement')

    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from erp5.component.document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {
          'ledger__uid': self.portal.portal_categories.ledger.automated.getUid(),
          'specialise__uid': business_process.getUid(),
          'activate_kw': {'tag': 'root_tag'}
        }}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            root_business_link.getUid(), business_process.getUid()),
          'after_tag': 'root_tag', 'activity': 'SQLQueue'}}],
        activate_value)

      open(build_simulator, 'w').truncate()
      open(activate_simulator, 'w').truncate()

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {
          'ledger__uid': self.portal.portal_categories.ledger.automated.getUid(),
          'specialise__uid': business_process.getUid(),
          'activate_kw': {'tag': 'lower_tag'}
        }}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            business_link.getUid(), business_process.getUid()),
          'after_tag': 'lower_tag', 'activity': 'SQLQueue'}}],
        activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)

  def test_SimulationMovement_buildSlapOS_script_withDelivery(self):
    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]

    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality=root_business_link.getRelativeUrl(),
        ledger='automated',
        delivery=delivery_line.getRelativeUrl(),
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality=business_link.getRelativeUrl(),
        delivery=delivery_line.getRelativeUrl(),
        ledger='automated',
        portal_type='Simulation Movement')

    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from erp5.component.document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

      open(build_simulator, 'w').write(repr([]))
      open(activate_simulator, 'w').write(repr([]))

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)


class TestSlapOSManageBuildingCalculatingSalePackingListAlarm(SlapOSTestCaseMixin):
  _delivery_portal_type = 'Sale Packing List'

  #################################################################
  # slapos_manage_building_calculating_delivery
  #################################################################
  def _test(self, state, test_function):
    delivery = self.portal.getDefaultModule(portal_type=self._delivery_portal_type).newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        ledger='automated',
        portal_type=self._delivery_portal_type)
    self.portal.portal_workflow._jumpToStateFor(delivery, state)
    with TemporaryAlarmScript(self.portal, 'Delivery_manageBuildingCalculatingDelivery', "''", attribute='title'):
      self.tic()
    test_function(
      self.portal.portal_alarms.slapos_manage_building_calculating_delivery,
      delivery,
      'Delivery_manageBuildingCalculatingDelivery',
      attribute='title'
    )

  def test_Delivery_manageBuildingCalculatingDelivery_alarm_building(self):
    self._test('building', self._test_alarm)

  def test_Delivery_manageBuildingCalculatingDelivery_alarm_calculating(self):
    self._test('calculating', self._test_alarm)

  def test_Delivery_manageBuildingCalculatingDelivery_alarm_diverged(self):
    self._test('diverged', self._test_alarm_not_visited)

  def test_Delivery_manageBuildingCalculatingDelivery_alarm_solved(self):
    self._test('solved', self._test_alarm_not_visited)

  #################################################################
  # Delivery_manageBuildingCalculatingDelivery
  #################################################################
  def _test_Delivery_manageBuildingCalculatingDelivery(self, state, empty=False):
    updateCausalityState_simulator = tempfile.mkstemp()[1]
    updateSimulation_simulator = tempfile.mkstemp()[1]

    delivery = self.portal.getDefaultModule(portal_type=self._delivery_portal_type).newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type=self._delivery_portal_type)
    self.portal.portal_workflow._jumpToStateFor(delivery, state)

    try:
      from erp5.component.document.Delivery import Delivery
      Delivery.original_updateCausalityState = Delivery.updateCausalityState
      Delivery.original_updateSimulation = Delivery.updateSimulation
      Delivery.updateCausalityState = Simulator(
          updateCausalityState_simulator, 'updateCausalityState')
      Delivery.updateSimulation = Simulator(
          updateSimulation_simulator, 'updateSimulation')

      delivery.Delivery_manageBuildingCalculatingDelivery()

      updateCausalityState_value = eval(open(updateCausalityState_simulator).read()) #pylint: disable=eval-used
      updateSimulation_value = eval(open(updateSimulation_simulator).read()) #pylint: disable=eval-used

      if empty:
        self.assertEqual([], updateCausalityState_value)
        self.assertEqual([], updateSimulation_value)
      else:
        self.assertEqual([{
          'recmethod': 'updateCausalityState',
          'recargs': (),
          'reckwargs': {'solve_automatically': True}}],
          updateCausalityState_value
        )
        self.assertEqual([{
          'recmethod': 'updateSimulation',
          'recargs': (),
          'reckwargs': {'expand_root': 1, 'expand_related': 1}}],
          updateSimulation_value
        )
    finally:
      Delivery.updateCausalityState = Delivery.original_updateCausalityState
      Delivery.updateSimulation = Delivery.original_updateSimulation
      delattr(Delivery, 'original_updateCausalityState')
      delattr(Delivery, 'original_updateSimulation')
      if os.path.exists(updateCausalityState_simulator):
        os.unlink(updateCausalityState_simulator)
      if os.path.exists(updateSimulation_simulator):
        os.unlink(updateSimulation_simulator)

  def test_Delivery_manageBuildingCalculatingDelivery_script_calculating(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('calculating')

  def test_Delivery_manageBuildingCalculatingDelivery_script_building(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('building')

  def test_Delivery_manageBuildingCalculatingDelivery_script_solved(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('solved', True)

  def test_Delivery_manageBuildingCalculatingDelivery_script_diverged(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('diverged', True)


class TestSlapOSManageBuildingCalculatingInternalPackingListAlarm(TestSlapOSManageBuildingCalculatingSalePackingListAlarm):
  _delivery_portal_type = 'Internal Packing List'


class TestSlapOSStopConfirmedAggregatedSaleInvoiceTransactionAlarm(SlapOSTestCaseMixin):
  destination_state = 'stopped'
  script = 'Delivery_stopConfirmedAggregatedSaleInvoiceTransaction'
  portal_type = 'Sale Invoice Transaction'
  alarm = 'slapos_stop_confirmed_aggregated_sale_invoice_transaction'

  #################################################################
  # slapos_stop_confirmed_aggregated_sale_invoice_transaction
  #################################################################
  def _test(self, simulation_state, causality_state, ledger, positive,
      delivery_date=DateTime('2012/04/22'),
      accounting_date=DateTime('2012/04/28')):

    @simulate(self.script,  '*args, **kwargs', """
if context.getTitle() == 'Not visited by %s':
  context.setTitle('Visited by %s') """ % (self.script, self.script))
    def _real(self, simulation_state, causality_state, ledger, positive,
          delivery_date,
          accounting_date):
      not_visited = 'Not visited by %s' % self.script
      visited = 'Visited by %s' % self.script
      module = self.portal.getDefaultModule(portal_type=self.portal_type)
      delivery = module.newContent(title=not_visited, start_date=delivery_date,
          ledger=ledger,
          portal_type=self.portal_type)
      _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
      _jumpToStateFor(delivery, simulation_state)
      _jumpToStateFor(delivery, causality_state)
      self.tic()

      alarm = getattr(self.portal.portal_alarms, self.alarm)
      alarm.activeSense(params=dict(accounting_date=accounting_date))
      self.tic()

      if positive:
        self.assertEqual(visited, delivery.getTitle())
      else:
        self.assertEqual(not_visited, delivery.getTitle())
    _real(self, simulation_state, causality_state, ledger, positive,
        delivery_date, accounting_date)

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_alarm_typical(self):
    self._test('confirmed', 'solved',
        'automated', True)

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_alarm_bad_ledger(self):
    self._test('confirmed', 'solved', None, False)

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_alarm_bad_simulation_state(self):
    self._test('started', 'solved',
        'automated', False)

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_alarm_bad_causality_state(self):
    self._test('confirmed', 'calculating',
        'automated', False)

  #################################################################
  # Delivery_stopConfirmedAggregatedSaleInvoiceTransaction
  #################################################################
  def _test_script(self, simulation_state, causality_state, ledger,
        destination_state, consistency_failure=False):
    module = self.portal.getDefaultModule(portal_type=self.portal_type)
    delivery = module.newContent(portal_type=self.portal_type,
        ledger=ledger,
        source_payment='foo',
        start_date=DateTime())
    _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
    _jumpToStateFor(delivery, simulation_state)
    _jumpToStateFor(delivery, causality_state)
    def checkConsistency(*args, **kwargs):
      if consistency_failure:
        return ['bad']
      else:
        return []
    try:
      from Products.ERP5Type.Core.Folder import Folder
      Folder.original_checkConsistency = Folder.checkConsistency
      Folder.checkConsistency = checkConsistency
      getattr(delivery, self.script)()
    finally:
      Folder.checkConsistency = Folder.original_checkConsistency
      delattr(Folder, 'original_checkConsistency')
    self.assertEqual(destination_state, delivery.getSimulationState())

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_script_typical(self):
    self._test_script('confirmed', 'solved',
        'automated',
        self.destination_state)

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_script_bad_ledger(self):
    self._test_script('confirmed', 'solved', None, 'confirmed')

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_script_bad_simulation_state(self):
    self._test_script('started', 'solved',
        'automated',
        'started')

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_script_bad_causality_state(self):
    self._test_script('confirmed', 'building',
        'automated',
        'confirmed')

  def test_Delivery_stopConfirmedAggregatedSaleInvoiceTransaction_script_bad_consistency(self):
    self._test_script('confirmed', 'solved',
        'automated',
        'confirmed', True)


class TestSlapOSGeneratePackingListFromTioXML(SlapOSTestCaseMixin):
  #################################################################
  # slapos_accounting_generate_packing_list_from_tioxml
  #################################################################
  def createTioXMLFile(self):
    document = self.portal.consumption_document_module.newContent(
      title=self.generateNewId(),
      reference="TESTTIOCONS-%s" % self.generateNewId(),
    )
    return document

  @expectedFailure
  def test_ComputerConsumptionTioXMLFile_solveInvoicingGeneration_alarm(self):
    document = self.createTioXMLFile()
    document.submit()
    self.tic()

    script_name = "ComputerConsumptionTioXMLFile_solveInvoicingGeneration"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_packing_list_from_tioxml

    self._test_alarm(
      alarm, document, script_name)

  def test_ComputerConsumptionTioXMLFile_solveInvoicingGeneration_alarm_not_submitted(self):
    document = self.createTioXMLFile()
    self.tic()
    
    script_name = "ComputerConsumptionTioXMLFile_solveInvoicingGeneration"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_packing_list_from_tioxml

    self._test_alarm_not_visited(
      alarm, document, script_name)


class TestSlapOSCancelSaleTnvoiceTransactionPaiedPaymentListAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_cancel_sale_invoice_transaction_paied_payment_list
  #################################################################
  def _test_payment_is_draft(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list,
      payment_transaction,
      "PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered"
    )

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isDraftPayzen(self):
    self._test_payment_is_draft(payment_mode="payzen")

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isDraftWeChat(self):
    self._test_payment_is_draft(payment_mode="wechat")

  def _test_payment_is_stopped(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    payment_transaction.setStartDate(DateTime())
    payment_transaction.confirm()
    payment_transaction.start()
    payment_transaction.stop()
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list,
      payment_transaction,
      "PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered"
    )

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isStoppedPayzen(self):
    self._test_payment_is_stopped(payment_mode="payzen")

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isStoppedWechat(self):
    self._test_payment_is_stopped(payment_mode="wechat")

  def _test_payment_is_started(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    payment_transaction.setStartDate(DateTime())
    payment_transaction.confirm()
    payment_transaction.start()
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list,
      payment_transaction,
      "PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered"
    )

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isStartedPayzen(self):
    self._test_payment_is_started(payment_mode="payzen")

  def test_PaymentTransaction_cancelIfSaleInvoiceTransactionIsLettered_alarm_isStartedWechat(self):
    self._test_payment_is_started(payment_mode="wechat")


class TestSlapOSSaleTradeConditionChangeRequestValidateAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_sale_trade_condition_change_request_validate_submitted
  # Alarm_validateSubmittedSaleTradeConditionChangeRequest
  #################################################################
  def _createSaleTradeConditionChangeRequest(self):
    return self.portal.sale_trade_condition_change_request_module.newContent(
      portal_type='Sale Trade Condition Change Request',
      title="Test STC change %s" % (self.generateNewId())
    )

  def _createCustomerPerson(self):
    return self.portal.person_module.newContent(
      portal_type='Person',
      title="Test customer %s" % (self.generateNewId())
    )

  def _createSellerOrganisation(self, currency):
    return self.portal.organisation_module.newContent(
      portal_type='Organisation',
      title="Test seller %s" % (self.generateNewId()),
      vat_code='1234567890',
      default_address_region='europe/france',
      price_currency_value=currency
    )

  def _createCurrency(self):
    return self.portal.currency_module.newContent(
      portal_type='Currency',
      title="Test currency %s" % (self.generateNewId())
    )

  def _createSaleTradeCondition(self, create_currency=True):
    if create_currency:
      currency = self._createCurrency()
    else:
      currency = None
    return self.portal.sale_trade_condition_module.newContent(
      portal_type='Sale Trade Condition',
      title="Test STC %s" % (self.generateNewId()),
      price_currency_value=currency,
      specialise='business_process_module/slapos_sale_subscription_business_process',
      trade_condition_type='manual'
    )

  def _getLastComment(self, document):
    return self.portal.portal_workflow.getInfoFor(ob=document,
                                          name='comment', wf_id='ticket_workflow')

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_alarm_notSubmitted(self):
    script_name = "SaleTradeConditionChangeRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_sale_trade_condition_change_request_validate_submitted
    self._test_alarm_not_visited(alarm, self._createSaleTradeConditionChangeRequest(), script_name)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_alarm_submitted(self):
    script_name = "SaleTradeConditionChangeRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_sale_trade_condition_change_request_validate_submitted
    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    self._test_alarm(alarm, change_request, script_name)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SaleTradeConditionChangeRequest_validateIfSubmitted,
      REQUEST={})

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_noSTC(self):
    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'No draft Sale Trade Condition found')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_nonDraftSTC(self):
    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(sale_trade_condition, 'validated')
    change_request.edit(specialise_value=sale_trade_condition)
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'No draft Sale Trade Condition found')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_firstTopLevelDraftSTC(self):
    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition()
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'invalidated')
    self.assertEqual(self._getLastComment(change_request), 'New STC')
    self.assertEqual(sale_trade_condition.getValidationState(), 'validated')
    self.assertEqual(result, sale_trade_condition)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCForSameDestination(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue()
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'There is a STC for the customer: %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCNotSpecialising(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer,
      destination_section_value=customer,
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Must specialise a similar STC')
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCSpecialisingACustomerSTC(self):
    customer = self._createCustomerPerson()
    first_sale_trade_condition = self._createSaleTradeCondition()
    first_sale_trade_condition.edit(
      destination_value=customer,
      destination_section_value=customer
    )
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    customer2 = self._createCustomerPerson()
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer2,
      destination_section_value=customer2,
      specialise_value=first_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Can not specialise a customer STC: %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCNotForCustomerSpecialising(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer,
      specialise_value=first_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Is not a customer STC: %s' % sale_trade_condition.getRelativeUrl())
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCSpecialisingChangingSource(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer,
      destination_section_value=customer,
      source_value=customer,
      specialise_value=first_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Can not change source STC: %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCSpecialisingChangingSourceSection(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    seller = self._createSellerOrganisation(first_sale_trade_condition.getPriceCurrencyValue())
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer,
      destination_section_value=customer,
      source_section_value=seller,
      specialise_value=first_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Can not change source section STC: %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_secondTopLevelDraftSTCSpecialising(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      destination_value=customer,
      destination_section_value=customer,
      specialise_value=first_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'invalidated')
    self.assertEqual(self._getLastComment(change_request), 'Specialising')
    self.assertEqual(sale_trade_condition.getValidationState(), 'validated')
    self.assertEqual(result, sale_trade_condition)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_tooManyPreviousVersion(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    second_sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    second_sale_trade_condition.edit(
      title=first_sale_trade_condition.getTitle()
    )
    self.portal.portal_workflow._jumpToStateFor(second_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      title=first_sale_trade_condition.getTitle()
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Too many previous version of the STC')
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_singlePreviousVersionWithoutChange(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      title=first_sale_trade_condition.getTitle()
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'invalidated')
    self.assertEqual(self._getLastComment(change_request), 'Expiring %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(first_sale_trade_condition.getValidationState(), 'validated')
    self.assertFalse(first_sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(sale_trade_condition.getValidationState(), 'validated')
    self.assertEqual(sale_trade_condition.getEffectiveDate(), first_sale_trade_condition.getExpirationDate())
    self.assertTrue(sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(result, sale_trade_condition)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_singlePreviousVersionWithUnexpectedChange(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    customer = self._createCustomerPerson()
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      title=first_sale_trade_condition.getTitle(),
      destination_value=customer
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'cancelled')
    self.assertEqual(self._getLastComment(change_request), 'Unhandled requested changes on: destination')
    self.assertEqual(sale_trade_condition.getValidationState(), 'draft')
    self.assertEqual(result, None)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_singlePreviousVersionChangingSeller(self):
    first_sale_trade_condition = self._createSaleTradeCondition()
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    seller = self._createSellerOrganisation(first_sale_trade_condition.getPriceCurrencyValue())
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      title=first_sale_trade_condition.getTitle(),
      source_section_value=seller
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'invalidated')
    self.assertEqual(self._getLastComment(change_request), 'Expiring %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(first_sale_trade_condition.getValidationState(), 'validated')
    self.assertFalse(first_sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(sale_trade_condition.getValidationState(), 'validated')
    self.assertEqual(sale_trade_condition.getEffectiveDate(), first_sale_trade_condition.getExpirationDate())
    self.assertTrue(sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(result, sale_trade_condition)

  def test_SaleTradeConditionChangeRequest_validateIfSubmitted_script_singlePreviousVersionUpdatingSpecialiseVersion(self):
    previous_date = DateTime('2024/01/01')
    first_specialise_sale_trade_condition = self._createSaleTradeCondition()
    first_specialise_sale_trade_condition.edit(
      expiration_date=previous_date
    )
    self.portal.portal_workflow._jumpToStateFor(first_specialise_sale_trade_condition, 'validated')
    second_specialise_sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    second_specialise_sale_trade_condition.edit(
      price_currency_value=first_specialise_sale_trade_condition.getPriceCurrencyValue(),
      title=first_specialise_sale_trade_condition.getTitle(),
      effective_date=previous_date
    )
    self.portal.portal_workflow._jumpToStateFor(second_specialise_sale_trade_condition, 'validated')


    first_sale_trade_condition = self._createSaleTradeCondition()
    first_sale_trade_condition.edit(
      specialise_value=first_specialise_sale_trade_condition
    )
    self.portal.portal_workflow._jumpToStateFor(first_sale_trade_condition, 'validated')
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      self.tic()

    change_request = self._createSaleTradeConditionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(change_request, 'submitted')
    sale_trade_condition = self._createSaleTradeCondition(create_currency=False)
    sale_trade_condition.edit(
      price_currency_value=first_sale_trade_condition.getPriceCurrencyValue(),
      title=first_sale_trade_condition.getTitle(),
      specialise_value=second_specialise_sale_trade_condition
    )
    change_request.edit(
      specialise_value=sale_trade_condition
    )
    result = change_request.SaleTradeConditionChangeRequest_validateIfSubmitted()
    self.assertEqual(change_request.getSimulationState(), 'invalidated')
    self.assertEqual(self._getLastComment(change_request), 'Expiring %s' % first_sale_trade_condition.getRelativeUrl())
    self.assertEqual(first_sale_trade_condition.getValidationState(), 'validated')
    self.assertFalse(first_sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(sale_trade_condition.getValidationState(), 'validated')
    self.assertEqual(sale_trade_condition.getEffectiveDate(), first_sale_trade_condition.getExpirationDate())
    self.assertTrue(sale_trade_condition.getExpirationDate() is None)
    self.assertEqual(result, sale_trade_condition)


class TestSlapOSOpenSaleOrderInvalidationAlarm(SlapOSTestCaseMixin):

  #################################################################
  # slapos_archive_open_sale_order_with_unused_item
  #################################################################
  def _createValidatedItemAndOpenSaleOrderLine(self, portal_type='Project'):
    subscription_item = self.portal.hosting_subscription_module.newContent(
      portal_type='Hosting Subscription',
    )
    subscription_item.validate()
    project = self.portal.getDefaultModule(portal_type).newContent(
      portal_type=portal_type,
    )
    project.validate()
    open_order = self.portal.open_sale_order_module.newContent(
      portal_type='Open Sale Order',
      title="Test no subscription %s" % (self.new_id, ),
      ledger='automated',
    )
    open_order_line = open_order.newContent(
      portal_type='Open Sale Order Line',
      aggregate_value=[project, subscription_item],
    )
    open_order.plan()
    open_order.validate()
    return project, open_order_line

  def test_OpenSaleOrderLine_archiveIfUnusedItem_alarm_fromInvalidatedProject(self):
    script_name = "OpenSaleOrderLine_archiveIfUnusedItem"
    alarm = self.portal.portal_alarms.slapos_archive_open_sale_order_with_unused_item

    project, open_order_line = self._createValidatedItemAndOpenSaleOrderLine()
    project.invalidate()
    self._test_alarm(alarm, open_order_line, script_name)

  def test_OpenSaleOrderLine_archiveIfUnusedItem_alarm_fromValidatedProject(self):
    script_name = "OpenSaleOrderLine_archiveIfUnusedItem"
    alarm = self.portal.portal_alarms.slapos_archive_open_sale_order_with_unused_item

    _, open_order_line = self._createValidatedItemAndOpenSaleOrderLine()
    self._test_alarm_not_visited(alarm, open_order_line, script_name)

  def test_OpenSaleOrderLine_archiveIfUnusedItem_alarm_fromInvalidatedProjectAndOrder(self):
    script_name = "OpenSaleOrderLine_archiveIfUnusedItem"
    alarm = self.portal.portal_alarms.slapos_archive_open_sale_order_with_unused_item

    project, open_order_line = self._createValidatedItemAndOpenSaleOrderLine()
    project.invalidate()
    open_order_line.getParentValue().invalidate()
    self._test_alarm_not_visited(alarm, open_order_line, script_name)

  def test_OpenSaleOrderLine_archiveIfUnusedItem_script_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.OpenSaleOrderLine_archiveIfUnusedItem,
      REQUEST={}
    )

  def test_OpenSaleOrderLine_archiveIfUnusedItem_script_invalidateOpenSaleOrder(self):
    project, open_order_line = self._createValidatedItemAndOpenSaleOrderLine()
    project.invalidate()
    open_order = open_order_line.getParentValue()
    hosting_subscription = open_order_line.getAggregateValue(portal_type='Hosting Subscription')
    fake_now = DateTime('2023/05/19')
    with PinnedDateTime(self, fake_now):
      result = open_order_line.OpenSaleOrderLine_archiveIfUnusedItem()
    self.assertEqual(result, open_order)
    self.assertEqual(open_order.getValidationState(), 'archived')
    self.assertEqual(open_order.getStopDate(), fake_now)
    self.assertEqual(hosting_subscription.getValidationState(), 'archived')

