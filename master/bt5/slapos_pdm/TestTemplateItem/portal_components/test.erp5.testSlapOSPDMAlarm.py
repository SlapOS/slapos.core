# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript

class TestSlapOSUpgradeDecisionProcess(SlapOSTestCaseMixin):

  def _makeUpgradeDecision(self, confirm=True):
    upgrade_decision = self.portal.\
       upgrade_decision_module.newContent(
         portal_type="Upgrade Decision",
         title="TESTUPDE-%s" % self.generateNewId())
    if confirm:
      upgrade_decision.confirm()
    return upgrade_decision

  def _makeInstanceTree(self, slap_state="start_requested"):
    instance_tree = self.portal\
      .instance_tree_module\
      .newContent(portal_type="Instance Tree")
    instance_tree.validate()
    new_id = self.generateNewId()
    instance_tree.edit(
        title= "Test hosting sub start %s" % new_id,
        reference="TESTHSS-%s" % new_id
    )
    self.portal.portal_workflow._jumpToStateFor(instance_tree, slap_state)

    return instance_tree

  def test_alarm_upgrade_decision_process_instance_tree(self):
    upgrade_decision = self._makeUpgradeDecision()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'"):
      upgrade_decision.start()
    self.tic()

    with TemporaryAlarmScript(self.portal, 'UpgradeDecision_processUpgrade'):
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_started.\
        activeSense()
      self.tic()

    self.assertEqual(
        'Visited by UpgradeDecision_processUpgrade',
        upgrade_decision.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_instance_tree_create_upgrade_decision(self):
    instance_tree = self._makeInstanceTree()
    self.tic()

    with TemporaryAlarmScript(self.portal, 'InstanceTree_createUpgradeDecision'):
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision.\
        activeSense()
      self.tic()

    self.assertEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_create_upgrade_decision_destroyed_instance_tree(self):
    instance_tree = self._makeInstanceTree(slap_state="destroy_requested")
    self.tic()

    with TemporaryAlarmScript(self.portal, 'InstanceTree_createUpgradeDecision'):
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision.\
        activeSense()
      self.tic()

    self.assertNotEqual('Visited by InstanceTree_createUpgradeDecision',
      instance_tree.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_destroy_unused_software_installation(self):
    software_installation = self.portal.software_installation_module.newContent(
      portal_type='Software Installation'
    )
    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_installation,
                                                'validated')
    self.tic()

    with TemporaryAlarmScript(self.portal, 'SoftwareInstallation_destroyIfUnused'):
      self.portal.portal_alarms.slapos_pdm_destroy_unused_software_installation.\
        activeSense()
      self.tic()

    self.assertEqual('Visited by SoftwareInstallation_destroyIfUnused',
      software_installation.workflow_history['edit_workflow'][-1]['comment'])