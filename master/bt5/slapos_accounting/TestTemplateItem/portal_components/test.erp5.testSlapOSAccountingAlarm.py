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

import transaction
from functools import wraps
from Products.ERP5Type.tests.utils import createZODBPythonScript
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, withAbort, TemporaryAlarmScript


import os
import tempfile
from DateTime import DateTime


class Simulator:
  def __init__(self, outfile, method, to_return=None):
    self.outfile = outfile
    open(self.outfile, 'w').write(repr([]))
    self.method = method
    self.to_return = to_return

  def __call__(self, *args, **kwargs):
    """Simulation Method"""
    old = open(self.outfile, 'r').read()
    if old:
      l = eval(old) #pylint: disable=eval-used
    else:
      l = []
    l.append({'recmethod': self.method,
      'recargs': args,
      'reckwargs': kwargs})
    open(self.outfile, 'w').write(repr(l))
    return self.to_return

def simulateByEditWorkflowMark(script_name):
  def wrapper(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
      if script_name in self.portal.portal_skins.custom.objectIds():
        raise ValueError('Precondition failed: %s exists in custom' % script_name)
      createZODBPythonScript(self.portal.portal_skins.custom,
                          script_name,
                          '*args, **kwargs',
                          '# Script body\n'
  """context.portal_workflow.doActionFor(context, action='edit_action', comment='Visited by %s') """ % script_name )
      transaction.commit()
      try:
        result = func(self, *args, **kwargs)
      finally:
        if script_name in self.portal.portal_skins.custom.objectIds():
          self.portal.portal_skins.custom.manage_delObjects(script_name)
        transaction.commit()
      return result
    return wrapped
  return wrapper

def simulateByTitlewMark(script_name):
  def wrapper(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
      if script_name in self.portal.portal_skins.custom.objectIds():
        raise ValueError('Precondition failed: %s exists in custom' % script_name)
      createZODBPythonScript(self.portal.portal_skins.custom,
                          script_name,
                          '*args, **kwargs',
                          '# Script body\n'
"""
if context.getTitle() == 'Not visited by %s':
  context.setTitle('Visited by %s')
""" %(script_name, script_name))
      transaction.commit()
      try:
        result = func(self, *args, **kwargs)
      finally:
        if script_name in self.portal.portal_skins.custom.objectIds():
          self.portal.portal_skins.custom.manage_delObjects(script_name)
        transaction.commit()
      return result
    return wrapped
  return wrapper


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
  @withAbort
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

  @withAbort
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

class TestSlapOSManageBuildingCalculatingDeliveryAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_manage_building_calculating_delivery
  #################################################################
  def _test(self, state, test_function):
    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        ledger='automated',
        portal_type='Sale Packing List')
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
  @withAbort
  def _test_Delivery_manageBuildingCalculatingDelivery(self, state, empty=False):
    updateCausalityState_simulator = tempfile.mkstemp()[1]
    updateSimulation_simulator = tempfile.mkstemp()[1]

    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type='Sale Packing List')
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
    @simulateByTitlewMark(self.script)
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
  @withAbort
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


class TestSlapOSGenerateConsumptionDeliveryFromTioXML(SlapOSTestCaseMixin):
  #################################################################
  # slapos_accounting_generate_packing_list_from_tioxml
  #################################################################
  def createTioXMLFile(self):
    document = self.portal.consumption_document_module.newContent(
      title=self.generateNewId(),
      reference="TESTTIOCONS-%s" % self.generateNewId(),
      portal_type="Computer Consumption TioXML File"
    )
    return document

  def test_ComputerConsumptionTioXMLFile_generateConsumptionDelivery_alarm(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      document = self.createTioXMLFile()
      document.submit()
      self.tic()

    script_name = "ComputerConsumptionTioXMLFile_generateConsumptionDelivery"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_from_tioxml

    self._test_alarm(
      alarm, document, script_name)

  def test_ComputerConsumptionTioXMLFile_generateConsumptionDelivery_alarm_not_submitted(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'", attribute='comment'):
      document = self.createTioXMLFile()
      self.tic()

    script_name = "ComputerConsumptionTioXMLFile_generateConsumptionDelivery"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_from_tioxml

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
