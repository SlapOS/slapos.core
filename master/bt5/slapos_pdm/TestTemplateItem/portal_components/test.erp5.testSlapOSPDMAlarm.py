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

  def test_alarm_compute_node_create_upgrade_decision(self):
    compute_node = self._makeComputeNode(allocation_scope = 'open/public')[0]
    compute_node2 = self._makeComputeNode(allocation_scope = 'open/personal')[0]
    compute_node3 = self._makeComputeNode(allocation_scope = 'open/friend')[0]
    self.tic()

    self._simulateScript('ComputeNode_checkAndCreateUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_compute_node_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('ComputeNode_checkAndCreateUpgradeDecision')

    self.assertEqual('Visited by ComputeNode_checkAndCreateUpgradeDecision',
      compute_node.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertEqual('Visited by ComputeNode_checkAndCreateUpgradeDecision',
      compute_node2.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual('Visited by ComputeNode_checkAndCreateUpgradeDecision',
      compute_node3.workflow_history['edit_workflow'][-1]['comment'])
  
  def test_alarm_instance_tree_create_upgrade_decision(self):
    instance_tree = self._makeInstanceTree()
    instance_tree2 = self._makeInstanceTree()
    instance_tree3 = self._makeInstanceTree()

    self.tic()

    self._simulateScript('InstanceTree_createUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('InstanceTree_createUpgradeDecision')

    self.assertEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree2.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree3.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_create_upgrade_decision_destroyed_instance_tree(self):
    instance_tree = self._makeInstanceTree(slap_state="destroy_requested")
    instance_tree2 = self._makeInstanceTree(slap_state="destroy_requested")
    self.tic()

    self._simulateScript('InstanceTree_createUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('InstanceTree_createUpgradeDecision')

    self.assertNotEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertNotEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree2.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_create_upgrade_decision_closed_compute_node(self):
    compute_node = self._makeComputeNode(allocation_scope='close/oudtated')[0]
    compute_node2 = self._makeComputeNode(allocation_scope='close/maintenance')[0]
    self.tic()

    self._simulateScript('ComputeNode_checkAndCreateUpgradeDecision', 'True')
    try:
      self.portal.portal_alarms.slapos_pdm_compute_node_create_upgrade_decision.\
        activeSense()
      self.tic()
    finally:
      self._dropScript('ComputeNode_checkAndCreateUpgradeDecision')

    self.assertNotEqual('Visited by ComputeNode_checkAndCreateUpgradeDecision',
      compute_node.workflow_history['edit_workflow'][-1]['comment'])
    
    self.assertNotEqual('Visited by ComputeNode_checkAndCreateUpgradeDecision',
      compute_node2.workflow_history['edit_workflow'][-1]['comment'])
