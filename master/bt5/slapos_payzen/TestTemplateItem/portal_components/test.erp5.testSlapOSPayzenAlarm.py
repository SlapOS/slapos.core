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

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
from Products.ERP5Type.tests.utils import createZODBPythonScript
from DateTime import DateTime

class TestSlapOSPayzenUpdateStartedPayment(SlapOSTestCaseMixinWithAbort):

  def test_not_started_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      )
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    transaction.PaymentTransaction_updateStatus()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_not_payzen_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    transaction.PaymentTransaction_updateStatus()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_not_registered_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    transaction.PaymentTransaction_updateStatus()
    self.assertEqual(transaction.getSimulationState(), 'started')

  def _simulatePaymentTransaction_createPaidPayzenEvent(self):
    script_name = 'PaymentTransaction_createPayzenEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_createPayzenEvent')

class Foo:
  def updateStatus(self):
    context.stop()
return Foo()
""" )
    self.commit()

  def _simulatePaymentTransaction_createNotPaidPayzenEvent(self):
    script_name = 'PaymentTransaction_createPayzenEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_createPayzenEvent')

class Foo:
  def updateStatus(self):
    pass
return Foo()
""")
    self.commit()

  def _dropPaymentTransaction_createPayzenEvent(self):
    script_name = 'PaymentTransaction_createPayzenEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_paid_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      start_date=DateTime(),
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    # Manually generate mapping
    transaction.PaymentTransaction_generatePayzenId()

    self._simulatePaymentTransaction_createPaidPayzenEvent()
    try:
      transaction.PaymentTransaction_updateStatus()
    finally:
      self._dropPaymentTransaction_createPayzenEvent()
    self.assertEqual(
        'Visited by PaymentTransaction_createPayzenEvent',
        transaction.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(
        "",
        transaction.workflow_history['edit_workflow'][-2]['comment'])
    self.assertEqual(transaction.getSimulationState(), 'stopped')

  def test_not_paid_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      start_date=DateTime(),
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    # Manually generate mapping
    transaction.PaymentTransaction_generatePayzenId()

    self._simulatePaymentTransaction_createNotPaidPayzenEvent()
    try:
      transaction.PaymentTransaction_updateStatus()
    finally:
      self._dropPaymentTransaction_createPayzenEvent()
    self.assertEqual(
        'Visited by PaymentTransaction_createPayzenEvent',
        transaction.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(transaction.getSimulationState(), 'started')

  def _simulatePaymentTransaction_updateStatus(self):
    script_name = 'PaymentTransaction_updateStatus'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_updateStatus') """ )
    self.commit()

  def _dropPaymentTransaction_updateStatus(self):
    script_name = 'PaymentTransaction_updateStatus'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_alarm_started_draft_payzen(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.tic()

    self._simulatePaymentTransaction_updateStatus()
    try:
      self.portal.portal_alarms.slapos_payzen_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateStatus()
    self.tic()
    self.assertEqual(
        'Visited by PaymentTransaction_updateStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_started(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      )
    self.tic()

    self._simulatePaymentTransaction_updateStatus()
    try:
      self.portal.portal_alarms.slapos_payzen_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_draft(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="payzen",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.portal.portal_workflow._jumpToStateFor(transaction, 'solved')
    self.tic()

    self._simulatePaymentTransaction_updateStatus()
    try:
      self.portal.portal_alarms.slapos_payzen_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_payzen(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.tic()

    self._simulatePaymentTransaction_updateStatus()
    try:
      self.portal.portal_alarms.slapos_payzen_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

