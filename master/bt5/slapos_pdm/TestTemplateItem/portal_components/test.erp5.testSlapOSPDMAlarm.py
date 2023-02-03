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

  def _makeInstanceTree(self, slap_state="start_requested"):
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title= "Test hosting sub start %s" % self.new_id,
        reference="TESTHSS-%s" % self.new_id,
    )
    self.portal.portal_workflow._jumpToStateFor(instance_tree, slap_state)

    return instance_tree

  def test_alarm_upgrade_decision_process_instance_tree(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_started,
      upgrade_decision,
      'UpgradeDecision_processUpgrade')

  def test_alarm_upgrade_decision_process_planned(self):
    upgrade_decision = self._makeUpgradeDecision(confirm=0)
    upgrade_decision.plan()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_planned,
      upgrade_decision,
      'UpgradeDecision_notify')

  def test_alarm_upgrade_decision_process_stopped(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_stopped,
      upgrade_decision,
      'UpgradeDecision_notifyDelivered')

  def _test_alarm_compute_node_create_upgrade_decision(self, allocation_scope):
    compute_node = self._makeComputeNode(allocation_scope=allocation_scope)[0]
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_compute_node_create_upgrade_decision,
      compute_node,
      'ComputeNode_checkAndCreateUpgradeDecision')

  def test_alarm_compute_node_create_upgrade_decision_public(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/public')

  def test_alarm_compute_node_create_upgrade_decision_personal(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/personal')

  def test_alarm_compute_node_create_upgrade_decision_friend(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/friend')

  def test_alarm_compute_node_create_upgrade_decision_subscription(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/subscription')

  def test_alarm_compute_node_create_upgrade_decision_subscription(self):
    self._test_alarm_compute_node_create_upgrade_decision('close/outdated')

  def test_alarm_compute_node_create_upgrade_decision_subscription(self):
    self._test_alarm_compute_node_create_upgrade_decision('close/maintanance')

  def test_alarm_compute_node_create_upgrade_decision_subscription(self):
    self._test_alarm_compute_node_create_upgrade_decision('close/termination')

  def test_alarm_instance_tree_create_upgrade_decision(self):
    instance_tree = self._makeInstanceTree()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision')

  def test_alarm_create_upgrade_decision_destroyed_instance_tree(self):
    instance_tree = self._makeInstanceTree(slap_state="destroy_requested")
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision')
