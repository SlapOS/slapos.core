# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSUpgradeDecisionProcess(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.new_id = self.generateNewId()

  def _makeUpgradeDecision(self, confirm=True):
    upgrade_decision = self.portal.\
       upgrade_decision_module.newContent(
         portal_type="Upgrade Decision",
         title="TESTUPDE-%s" % self.new_id)
    if confirm:
      upgrade_decision.confirm()
    return upgrade_decision

  def _makeHostingSubscription(self, slap_state="start_requested"):
    hosting_subscription = self.portal\
      .hosting_subscription_module.template_hosting_subscription\
      .Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    hosting_subscription.edit(
        title= "Test hosting sub start %s" % self.new_id,
        reference="TESTHSS-%s" % self.new_id,
    )
    self.portal.portal_workflow._jumpToStateFor(hosting_subscription, slap_state)

    return hosting_subscription

  def test_alarm_upgrade_decision_process_hosting_subscription(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    self.tic()

    self._simulateScript('UpgradeDecision_processUpgrade', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_started.activeSense()
      self.tic()
    finally:
      self._dropScript('UpgradeDecision_processUpgrade')
    self.assertEqual(
        'Visited by UpgradeDecision_processUpgrade',
        upgrade_decision.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_upgrade_decision_process_planned(self):
    upgrade_decision = self._makeUpgradeDecision(confirm=0)
    upgrade_decision.plan()
    self.tic()

    self._simulateScript('UpgradeDecision_notify', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_planned.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('UpgradeDecision_notify')

    self.assertEqual('Visited by UpgradeDecision_notify',
      upgrade_decision.workflow_history['edit_workflow'][-1]['comment'])
    

  def test_alarm_upgrade_decision_process_stopped(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()

    self._simulateScript('UpgradeDecision_notifyDelivered',  'True')
    try:
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_stopped.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('UpgradeDecision_notifyDelivered')

    self.assertEqual('Visited by UpgradeDecision_notifyDelivered',
      upgrade_decision.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_computer_create_upgrade_decision(self):
    computer = self._makeComputer(allocation_scope = 'open/public')[0]
    computer2 = self._makeComputer(allocation_scope = 'open/personal')[0]
    computer3 = self._makeComputer(allocation_scope = 'open/friend')[0]
    self.tic()

    self._simulateScript('Computer_checkAndCreateUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_computer_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('Computer_checkAndCreateUpgradeDecision')

    self.assertEqual('Visited by Computer_checkAndCreateUpgradeDecision',
      computer.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertEqual('Visited by Computer_checkAndCreateUpgradeDecision',
      computer2.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual('Visited by Computer_checkAndCreateUpgradeDecision',
      computer3.workflow_history['edit_workflow'][-1]['comment'])
  
  def test_alarm_hosting_subscription_create_upgrade_decision(self):
    hosting_subscription = self._makeHostingSubscription()
    hosting_subscription2 = self._makeHostingSubscription()
    hosting_subscription3 = self._makeHostingSubscription()

    self.tic()

    self._simulateScript('HostingSubscription_createUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_hosting_subscription_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('HostingSubscription_createUpgradeDecision')

    self.assertEqual('Visited by HostingSubscription_createUpgradeDecision',
      hosting_subscription.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertEqual('Visited by HostingSubscription_createUpgradeDecision',
      hosting_subscription2.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual('Visited by HostingSubscription_createUpgradeDecision',
      hosting_subscription3.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_create_upgrade_decision_destroyed_hosting_subscription(self):
    hosting_subscription = self._makeHostingSubscription(slap_state="destroy_requested")
    hosting_subscription2 = self._makeHostingSubscription(slap_state="destroy_requested")
    self.tic()

    self._simulateScript('HostingSubscription_createUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_hosting_subscription_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('HostingSubscription_createUpgradeDecision')

    self.assertNotEqual('Visited by HostingSubscription_createUpgradeDecision',
      hosting_subscription.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertNotEqual('Visited by HostingSubscription_createUpgradeDecision',
      hosting_subscription2.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_create_upgrade_decision_closed_computer(self):
    computer = self._makeComputer(allocation_scope='close/oudtated')[0]
    computer2 = self._makeComputer(allocation_scope='close/maintenance')[0]
    self.tic()

    self._simulateScript('Computer_checkAndCreateUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_computer_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('Computer_checkAndCreateUpgradeDecision')

    self.assertNotEqual('Visited by Computer_checkAndCreateUpgradeDecision',
      computer.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertNotEqual('Visited by Computer_checkAndCreateUpgradeDecision',
      computer2.workflow_history['edit_workflow'][-1]['comment'])
