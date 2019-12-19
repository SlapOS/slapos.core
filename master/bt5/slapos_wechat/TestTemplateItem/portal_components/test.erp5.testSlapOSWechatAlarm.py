# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
from Products.ERP5Type.tests.utils import createZODBPythonScript
from DateTime import DateTime

class TestSlapOSWechatUpdateConfirmedPayment(SlapOSTestCaseMixinWithAbort):

  def _simulatePaymentTransaction_startWechatPayment(self):
    script_name = 'PaymentTransaction_startWechatPayment'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_startWechatPayment') """ )
    self.commit()

  def _dropPaymentTransaction_startWechatPayment(self):
    script_name = 'PaymentTransaction_startWechatPayment'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_alarm_confirmed_draft_wechat(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')
    self.tic()

    self._simulatePaymentTransaction_startWechatPayment()
    try:
      self.portal.portal_alarms.slapos_wechat_update_confirmed_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_startWechatPayment()
    self.tic()
    self.assertEqual(
        'Visited by PaymentTransaction_startWechatPayment',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_confirmed(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.tic()

    self._simulatePaymentTransaction_startWechatPayment()
    try:
      self.portal.portal_alarms.slapos_wechat_update_confirmed_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_startWechatPayment()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_startWechatPayment',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_draft(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')
    self.portal.portal_workflow._jumpToStateFor(transaction, 'solved')
    self.tic()

    self._simulatePaymentTransaction_startWechatPayment()
    try:
      self.portal.portal_alarms.slapos_wechat_update_confirmed_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_startWechatPayment()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_startWechatPayment',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_wechat(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')
    self.tic()

    self._simulatePaymentTransaction_startWechatPayment()
    try:
      self.portal.portal_alarms.slapos_wechat_update_confirmed_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_startWechatPayment()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_startWechatPayment',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def _simulatePaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""return 1""")
    self.commit()

  def _simulatePaymentTransaction_getZeroTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""return 0""")
    self.commit()

  def _dropPaymentTransaction_getTotalPayablePrice(self):
    script_name = 'PaymentTransaction_getTotalPayablePrice'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_not_confirmed_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    self._simulatePaymentTransaction_getTotalPayablePrice()
    try:
      transaction.PaymentTransaction_startWechatPayment()
    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_not_wechat_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    self._simulatePaymentTransaction_getTotalPayablePrice()
    try:
      transaction.PaymentTransaction_startWechatPayment()
    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_zero_amount_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()

    self._simulatePaymentTransaction_getZeroTotalPayablePrice()
    try:
      transaction.PaymentTransaction_startWechatPayment()
    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_expected_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'confirmed')

    self._simulatePaymentTransaction_getTotalPayablePrice()
    try:
      transaction.PaymentTransaction_startWechatPayment()
    finally:
      self._dropPaymentTransaction_getTotalPayablePrice()
    self.assertEqual(transaction.getSimulationState(), 'started')


class TestSlapOSWechatUpdateStartedPayment(SlapOSTestCaseMixinWithAbort):

  def test_not_started_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    transaction.PaymentTransaction_updateWechatPaymentStatus()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_not_wechat_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    simulation_state = transaction.getSimulationState()
    modification_date = transaction.getModificationDate()
    transaction.PaymentTransaction_updateWechatPaymentStatus()
    self.assertEqual(transaction.getSimulationState(), simulation_state)
    self.assertEqual(transaction.getModificationDate(), modification_date)

  def test_not_registered_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    transaction.PaymentTransaction_updateWechatPaymentStatus()
    self.assertEqual(transaction.getSimulationState(), 'started')

  def _simulatePaymentTransaction_createPaidWechatEvent(self):
    script_name = 'PaymentTransaction_createWechatEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_createWechatEvent')

class Foo:
  def updateStatus(self):
    context.stop()
return Foo()
""" )
    self.commit()

  def _simulatePaymentTransaction_createNotPaidWechatEvent(self):
    script_name = 'PaymentTransaction_createWechatEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_createWechatEvent')

class Foo:
  def updateStatus(self):
    pass
return Foo()
""" )
    self.commit()

  def _dropPaymentTransaction_createWechatEvent(self):
    script_name = 'PaymentTransaction_createWechatEvent'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_paid_payment(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      start_date=DateTime(),
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    # Manually generate mapping
    transaction.PaymentTransaction_generateWechatId()

    self._simulatePaymentTransaction_createPaidWechatEvent()
    try:
      transaction.PaymentTransaction_updateWechatPaymentStatus()
    finally:
      self._dropPaymentTransaction_createWechatEvent()
    self.assertEqual(
        'Visited by PaymentTransaction_createWechatEvent',
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
      payment_mode="wechat",
      start_date=DateTime(),
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')

    # Manually generate mapping
    transaction.PaymentTransaction_generateWechatId()

    self._simulatePaymentTransaction_createNotPaidWechatEvent()
    try:
      transaction.PaymentTransaction_updateWechatPaymentStatus()
    finally:
      self._dropPaymentTransaction_createWechatEvent()
    self.assertEqual(
        'Visited by PaymentTransaction_createWechatEvent',
        transaction.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(transaction.getSimulationState(), 'started')

  def _simulatePaymentTransaction_updateWechatPaymentStatus(self):
    script_name = 'PaymentTransaction_updateWechatPaymentStatus'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by PaymentTransaction_updateWechatPaymentStatus') """ )
    self.commit()

  def _dropPaymentTransaction_updateWechatPaymentStatus(self):
    script_name = 'PaymentTransaction_updateWechatPaymentStatus'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    self.commit()

  def test_alarm_started_draft_wechat(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.tic()

    self._simulatePaymentTransaction_updateWechatPaymentStatus()
    try:
      self.portal.portal_alarms.slapos_wechat_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateWechatPaymentStatus()
    self.tic()
    self.assertEqual(
        'Visited by PaymentTransaction_updateWechatPaymentStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_started(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.tic()

    self._simulatePaymentTransaction_updateWechatPaymentStatus()
    try:
      self.portal.portal_alarms.slapos_wechat_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateWechatPaymentStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateWechatPaymentStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_draft(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode="wechat",
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.portal.portal_workflow._jumpToStateFor(transaction, 'solved')
    self.tic()

    self._simulatePaymentTransaction_updateWechatPaymentStatus()
    try:
      self.portal.portal_alarms.slapos_wechat_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateWechatPaymentStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateWechatPaymentStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_wechat(self):
    new_id = self.generateNewId()
    transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      )
    self.portal.portal_workflow._jumpToStateFor(transaction, 'started')
    self.tic()

    self._simulatePaymentTransaction_updateWechatPaymentStatus()
    try:
      self.portal.portal_alarms.slapos_wechat_update_started_payment.activeSense()
      self.tic()
    finally:
      self._dropPaymentTransaction_updateWechatPaymentStatus()
    self.tic()
    self.assertNotEqual(
        'Visited by PaymentTransaction_updateWechatPaymentStatus',
        transaction.workflow_history['edit_workflow'][-1]['comment'])