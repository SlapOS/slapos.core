# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, \
  TemporaryAlarmScript, SlapOSTestCaseMixinWithAbort
import time

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

  #################################################################
  # InstanceTree_createUpgradeDecision
  #################################################################
  def test_createUpgradeDecision_alarm_validated(self):
    instance_tree = self._makeInstanceTree()
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision'
    )

  def test_createUpgradeDecision_alarm_destroyed(self):
    instance_tree = self._makeInstanceTree(slap_state="destroy_requested")
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision'
    )

  def test_createUpgradeDecision_alarm_optimized(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              fake_return=None, attribute=False):
      _, _, _, _, _, instance_tree = self.bootstrapAllocableInstanceTree(has_allocation_supply=True)
      self.tic()
    allocation_supply = self.portal.portal_catalog.getResultValue(
      portal_type='Allocation Supply',
      destination_project__uid=instance_tree.getFollowUpUid()
    )

    # Sadly, indexation timestamp is not impacted by PinnedDateTime
    # so, wait a bit...
    time.sleep(1)

    alarm = self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision
    params = {'Base_reindexAndSenseAlarm': True}
    # Fake previous alarm run
    alarm.Alarm_storeCurrentRunDateAndReturnPreviousRunDate(params)
    self.tic()

    # If the object was not reindexed since last alarm run,
    # the alarm does not browse it anymore
    self._test_alarm_not_visited(
      alarm,
      instance_tree,
      'InstanceTree_createUpgradeDecision',
      sense_kw={'params': params}
    )

    allocation_supply.reindexObject()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                              fake_return=None, attribute=False):
      self.tic()

    # But it is was reindexed, in this case, it is checked
    self._test_alarm(
      alarm,
      instance_tree,
      'InstanceTree_createUpgradeDecision',
      sense_kw={'params': params}
    )

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


class TestSlaposCrmCheckStoppedEventFromUpgradeDecisionToDeliver(SlapOSTestCaseMixinWithAbort):

  event_portal_type = 'Web Message'

  def _makeUpgradeDecision(self, confirm=True):
    upgrade_decision = self.portal.\
       upgrade_decision_module.newContent(
         portal_type="Upgrade Decision",
         title="TESTUPDE-%s" % self.generateNewId())
    if confirm:
      upgrade_decision.confirm()
    return upgrade_decision

  def _makeEvent(self, follow_up_value):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type=self.event_portal_type,
      title='Test %s %s' % (self.event_portal_type, new_id),
      follow_up_value=follow_up_value
    )

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_alarm_stopped(self):
    upgrade_decision = self._makeUpgradeDecision()
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_pdm_check_stopped_event_from_upgrade_decision_to_deliver
    self._test_alarm(alarm, event, "Event_checkStoppedFromUpgradeDecisionToDeliver")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_alarm_delivered(self):
    upgrade_decision = self._makeUpgradeDecision()
    event = self._makeEvent(upgrade_decision)
    event.stop()
    event.deliver()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
       slapos_pdm_check_stopped_event_from_upgrade_decision_to_deliver
    self._test_alarm_not_visited(alarm, event,
      "Event_checkStoppedFromUpgradeDecisionToDeliver")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_alarm_invalidatedWithoutTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    event = self._makeEvent(upgrade_decision)
    event.setFollowUp(None)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_pdm_check_stopped_event_from_upgrade_decision_to_deliver
    self._test_alarm_not_visited(alarm, event,
      "Event_checkStoppedFromUpgradeDecisionToDeliver")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_script_deliveredTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'"):
      upgrade_decision.start()
    upgrade_decision.deliver()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "delivered")
    event.Event_checkStoppedFromUpgradeDecisionToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(upgrade_decision.getSimulationState(), "delivered")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_script_rejectTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.reject()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "rejected")
    event.Event_checkStoppedFromUpgradeDecisionToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(upgrade_decision.getSimulationState(), "rejected")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_script_cancelTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.cancel()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "cancelled")
    event.Event_checkStoppedFromUpgradeDecisionToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(upgrade_decision.getSimulationState(), "cancelled")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_script_startedTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'"):
      upgrade_decision.start()
      self.tic()
    time.sleep(1)
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "started")
    event.Event_checkStoppedFromUpgradeDecisionToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "started")

  def test_Event_checkStoppedFromUpgradeDecisionToDeliver_script_stopTicket(self):
    upgrade_decision = self._makeUpgradeDecision()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm', "'disabled'"):
      upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(upgrade_decision)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "stopped")
    event.Event_checkStoppedFromUpgradeDecisionToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(upgrade_decision.getSimulationState(), "stopped")
