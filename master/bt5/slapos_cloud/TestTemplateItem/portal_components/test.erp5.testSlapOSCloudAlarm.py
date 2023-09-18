# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
import transaction
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript
from zExceptions import Unauthorized
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate


class TestSlapOSCoreSlapOSAssertInstanceTreeSuccessorAlarm(SlapOSTestCaseMixin):
  launch_caucase = 1
  #################################################################
  # slapos_assert_instance_tree_successor
  #################################################################
  def test_InstanceTree_assertSuccessor_alarm_orphaned(self):
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree'
    )
    instance_tree.validate()
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_assert_instance_tree_successor,
      instance_tree,
      'InstanceTree_assertSuccessor'
    )

  def test_InstanceTree_assertSuccessor_alarm_renamed(self):
    instance_tree = self.addInstanceTree()
    instance_tree.getSuccessorValue().edit(title=self.generateNewSoftwareTitle())
    self._test_alarm(
      self.portal.portal_alarms.slapos_assert_instance_tree_successor,
      instance_tree,
      'InstanceTree_assertSuccessor'
    )

  def test_InstanceTree_assertSuccessor_alarm_not_renamed(self):
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_assert_instance_tree_successor,
      self.addInstanceTree(),
      'InstanceTree_assertSuccessor'
    )

  #################################################################
  # InstanceTree_assertSuccessor
  #################################################################
  def test_InstanceTree_assertSuccessor_script_renamed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.edit(title=self.generateNewSoftwareTitle())
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertNotEqual(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.InstanceTree_assertSuccessor()

    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertIn(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_script_renamedAndStopped(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.edit(title=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'stop_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertNotIn(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.InstanceTree_assertSuccessor()

    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertIn(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_script_renamedAndDestroyed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.edit(title=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'destroy_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertNotIn(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.InstanceTree_assertSuccessor()

    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertFalse(instance_tree.getTitle() in
        instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_script_archived(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.edit(title=self.generateNewSoftwareTitle())
    instance_tree.archive()
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertNotIn(instance_tree.getTitle(), instance_tree.getSuccessorTitleList())

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      instance_tree.InstanceTree_assertSuccessor()

    self.assertNotEqual(instance_tree.getTitle(), software_instance.getTitle())
    self.assertFalse(instance_tree.getTitle() in
        instance_tree.getSuccessorTitleList())


class TestSlapOSFreeComputePartitionAlarm(SlapOSTestCaseMixin):

  launch_caucase = 1
  #################################################################
  # slapos_free_compute_partition
  #################################################################
  def test_SoftwareInstance_tryToUnallocatePartition_alarm_allocated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    # invalidate transition triggers the alarm
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')

    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_free_compute_partition,
      software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_SoftwareInstance_tryToUnallocatePartition_alarm_sharedAndAllocated(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    # invalidate transition triggers the alarm
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')

    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_free_compute_partition,
      software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_SoftwareInstance_tryToUnallocatePartition_alarm_unallocated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    # invalidate transition triggers the alarm
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')

    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_SoftwareInstance_tryToUnallocatePartition_alarm_allocatedAndValidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')

    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_SoftwareInstance_tryToUnallocatePartition_alarm_allocatedAndStarted(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  #################################################################
  # SoftwareInstance_tryToUnallocatePartition
  #################################################################
  def test_SoftwareInstance_tryToUnallocatePartition_script_allocated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')
    self.tic()

    software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.assertEqual(None, software_instance.getAggregate())
    self.assertEqual('free', partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_script_sharedAndAllocated(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')
    self.tic()

    software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.assertEqual(None, software_instance.getAggregate())
    self.assertEqual('free', partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_script_concurrency(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'invalidated')
    self.tic()

    partition.activate(tag="allocate_%s" % partition.getRelativeUrl()\
        ).getId()
    transaction.commit()
    software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
                    software_instance.getAggregate())
    self.assertEqual('busy', partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_script_twoInstances(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())
    instance_tree2 = self.addInstanceTree(project=instance_tree.getFollowUpValue())
    software_instance2 = instance_tree2.getSuccessorValue()

    self.tic()

    try:
      # Prevent calling interaction workflows
      software_instance.setCategoryList(
        software_instance.getCategoryList() + ['aggregate/%s' % partition.getRelativeUrl()]
        )
      software_instance2.setCategoryList(
        software_instance2.getCategoryList() + ['aggregate/%s' % partition.getRelativeUrl()]
      )
      self.portal.portal_workflow._jumpToStateFor(partition,
          'busy')
      self.portal.portal_workflow._jumpToStateFor(software_instance,
          'destroy_requested')
      self.portal.portal_workflow._jumpToStateFor(software_instance,
          'invalidated')
      self.tic()

      software_instance.SoftwareInstance_tryToUnallocatePartition()
      self.assertEqual(None, software_instance.getAggregate())
      self.assertEqual('busy', partition.getSlapState())
      self.assertEqual(partition.getRelativeUrl(), software_instance2.getAggregate())
    except:
      # 2 instances linked to a partition crashes _fillComputeNodeInformationCache
      # activity. Clean up to not impact the other tests
      software_instance2.setAggregate(None)
      raise
    finally:
      software_instance2.setAggregate(None)
    self.tic()

  def test_SoftwareInstance_tryToUnallocatePartition_script_notDestroyed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.tic()

    software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.assertEqual(partition.getRelativeUrl(), software_instance.getAggregate())
    self.assertEqual('busy', partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_script_notInvalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())

    software_instance.setAggregateValue(partition)
    partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')
    self.tic()

    software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.assertEqual(partition.getRelativeUrl(), software_instance.getAggregate())
    self.assertEqual('busy', partition.getSlapState())


class TestSlapOSGarbageCollectDestroyedRootTreeAlarm(SlapOSTestCaseMixin):
  launch_caucase = 1
  #################################################################
  # slapos_garbage_collect_destroyed_root_tree
  #################################################################
  def test_SoftwareInstance_tryToGarbageCollect_alarm_archived(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.archive()
    self._test_alarm(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  def test_SoftwareInstance_tryToGarbageCollect_alarm_sharedAndArchived(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.archive()
    self._test_alarm(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  def test_SoftwareInstance_tryToGarbageCollect_alarm_invalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.archive()
    software_instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  def test_SoftwareInstance_tryToGarbageCollect_alarm_notArchived(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  #################################################################
  # SoftwareInstance_tryToGarbageCollect
  #################################################################
  def test_SoftwareInstance_tryToGarbageCollect_script_destroyed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.archive()
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'destroy_requested')
    self.assertEqual('validated',
        software_instance.getValidationState())

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollect()

    self.assertEqual('destroy_requested',
        software_instance.getSlapState())
    self.assertEqual('validated',
        software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_script_archived(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.archive()

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollect()

    self.assertEqual('start_requested',
        software_instance.getSlapState())
    self.assertEqual('validated',
        software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_script_notArchived(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'destroy_requested')

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollect()
    self.assertEqual('start_requested',
        software_instance.getSlapState())
    self.assertEqual('validated',
        software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_script_unlinkedSuccessor(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    instance_tree.edit(successor_list=[])
    instance_tree.archive()
    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'destroy_requested')

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollect()

    self.assertEqual('destroy_requested',
        software_instance.getSlapState())
    self.assertEqual('validated',
        software_instance.getValidationState())


class TestSlapOSUpdateComputeNodeCapacityScopeAlarm(SlapOSTestCaseMixin):
  launch_caucase = 1 
  #################################################################
  # slapos_update_compute_node_capacity_scope
  #################################################################
  def test_ComputeNode_checkAndUpdateCapacityScope_alarm_open(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(
      allocation_scope='open',
    )
    self._test_alarm(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

  def test_ComputeNode_checkAndUpdateCapacityScope_alarm_close(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(
      allocation_scope='close',
    )
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

  def test_ComputeNode_checkAndUpdateCapacityScope_alarm_invalidated(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.invalidate()
    compute_node.edit(
      allocation_scope='open',
    )
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

  #################################################################
  # ComputeNode_checkAndUpdateCapacityScope
  #################################################################
  def test_ComputeNode_checkAndUpdateCapacityScope_script_open(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus("#access ok")
    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', compute_node.getCapacityScope())

  def addComputerModel(self, capacity_quantity=None):
    return self.portal.computer_model_module.newContent(
      portal_type="Computer Model",
      reference='TESTCM-%s' % self.generateNewId(),
      capacity_quantity=capacity_quantity
    )

  def test_ComputeNode_checkAndUpdateCapacityScope_script_model(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus("#access ok")

    computer_model = self.addComputerModel(9999)
    compute_node.edit(specialise_value=computer_model, capacity_quantity=None)

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', compute_node.getCapacityScope())
    self.assertEqual(computer_model.getCapacityQuantity(),
                     compute_node.getCapacityQuantity())

  def test_ComputeNode_checkAndUpdateCapacityScope_script_modelNoCapacity(self):
    compute_node, partition = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus("#access ok")

    computer_model = self.addComputerModel(1)
    compute_node.edit(specialise_value=computer_model, capacity_quantity=None)

    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.tic()

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', compute_node.getCapacityScope())
    self.assertEqual('Compute Node capacity limit exceeded',
        compute_node.workflow_history['edit_workflow'][-1]['comment'])
    self.assertEqual(computer_model.getCapacityQuantity(),
                     compute_node.getCapacityQuantity())

  def test_ComputeNode_checkAndUpdateCapacityScope_script_modelHasCapacity(self):
    # If capacity is set on compute_node, model value is ignored.
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus("#access ok")

    computer_model = self.addComputerModel(1)
    compute_node.edit(specialise_value=computer_model, capacity_quantity=2)

    self.tic()

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', compute_node.getCapacityScope())
    self.assertEqual(2,
                     compute_node.getCapacityQuantity())


  def test_ComputeNode_checkAndUpdateCapacityScope_script_withOldAccess(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    try:
      self.pinDateTime(addToDate(DateTime(),to_add={'minute': -11}))
      compute_node.setAccessStatus("#access ok")
    finally:
      self.unpinDateTime()

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', compute_node.getCapacityScope())
    self.assertEqual("Compute Node didn't contact for more than 10 minutes",
        compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_script_noCapacityQuantity(self):
    compute_node, partition = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus("#access ok")
    compute_node.edit(capacity_quantity=1)

    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.tic()

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', compute_node.getCapacityScope())
    self.assertEqual('Compute Node capacity limit exceeded',
        compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_script_noAccess(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', compute_node.getCapacityScope())
    self.assertEqual("Compute Node didn't contact the server",
        compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_script_capacityClose(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.setAccessStatus("#access ok")
    compute_node.edit(capacity_scope='close')

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', compute_node.getCapacityScope())

  def test_ComputeNode_checkAndUpdateCapacityScope_script_withError(self):
    compute_node, _ = self.addComputeNodeAndPartition()
    compute_node.edit(allocation_scope='open')
    compute_node.edit(capacity_scope='open')
    compute_node.setAccessStatus('#error not ok')

    compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', compute_node.getCapacityScope())
    self.assertEqual("Compute Node reported an error",
        compute_node.workflow_history['edit_workflow'][-1]['comment'])


class TestSlapOSGarbageCollectStoppedRootTreeAlarm(SlapOSTestCaseMixin):
  launch_caucase = 1 
  #################################################################
  # slapos_stop_collect_instance
  #################################################################
  def test_SoftwareInstance_tryToStopCollect_alarm(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self._test_alarm(
      self.portal.portal_alarms.slapos_stop_collect_instance,
      software_instance,
      'SoftwareInstance_tryToStopCollect'
    )

  def test_SoftwareInstance_tryToStopCollect_alarm_invalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_stop_collect_instance,
      software_instance,
      'SoftwareInstance_tryToStopCollect'
    )

  #################################################################
  # SoftwareInstance_tryToStopCollect
  #################################################################
  def test_SoftwareInstance_tryToStopCollect_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SoftwareInstance_tryToStopCollect,
      REQUEST={})

  def test_SoftwareInstance_tryToStopCollect_script_startedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'stop_requested')
    self.assertEqual('start_requested', software_instance.getSlapState())

    software_instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('stop_requested', software_instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_script_destroyedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'stop_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance,
        'destroy_requested')

    software_instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('destroy_requested', software_instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_script_startedInstanceTree(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.assertEqual('start_requested', instance_tree.getSlapState())
    self.assertEqual('start_requested', software_instance.getSlapState())

    software_instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('start_requested', software_instance.getSlapState())


class TestSlapOSGarbageCollectNonAllocatedRootTreeAlarm(SlapOSTestCaseMixin):
  launch_caucase = 1 
  #################################################################
  # slapos_garbage_collect_non_allocated_root_tree
  #################################################################
  def test_tryToGarbageCollectNonAllocatedRootTree_alarm(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self._test_alarm(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )

  def test_tryToGarbageCollectNonAllocatedRootTree_alarm_invalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )

  def test_tryToGarbageCollectNonAllocatedRootTree_alarm_allocated(self):
    _, partition = self.addComputeNodeAndPartition()
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      software_instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )

  #################################################################
  # SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree
  #################################################################
  def test_tryToGarbageCollectNonAllocatedRootTree_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree,
      REQUEST={})

  def test_tryToGarbageCollectNonAllocatedRootTree_script_invalidatedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.invalidate()

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_destroyedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_allocatedInstance(self):
    _, partition = self.addComputeNodeAndPartition()
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_noAllocationTryFound(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_recentAllocationTryFound(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    }]

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_oldAllocationTryFound(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.tic()

    software_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    }]
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance_tree.getSlapState())
    self.assertEqual('archived', instance_tree.getValidationState())
    self.assertEqual('start_requested', software_instance.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_recentAllocationTryFoundAllocationDisallowed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    software_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    }]

    self.tic()
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', software_instance.getSlapState())
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_oldAllocationTryFoundAllocationDisallowed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.tic()

    software_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    }]
    software_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance_tree.getSlapState())
    self.assertEqual('archived', instance_tree.getValidationState())
    self.assertEqual('start_requested', software_instance.getSlapState())


  def test_tryToGarbageCollectNonAllocatedRootTree_script_complexTree(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title="another %s" % instance_tree.getTitle(),
      state='started'
    )
    software_instance.requestInstance(**request_kw)
    sub_instance = software_instance.getSuccessorValue()
    self.tic()
    sub_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    }]

    sub_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollectNonAllocatedRootTree_script_complexTreeAllocationDisallowed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title="another %s" % instance_tree.getTitle(),
      state='started'
    )
    software_instance.requestInstance(**request_kw)
    sub_instance = software_instance.getSuccessorValue()
    self.tic()
    sub_instance.workflow_history['edit_workflow'] = [{
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    }]

    sub_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance_tree.getSlapState())


class TestSlapOSInvalidateDestroyedInstance(SlapOSTestCaseMixin):
  launch_caucase = 1 
  #################################################################
  # slapos_cloud_invalidate_destroyed_instance
  #################################################################
  def test_tryToInvalidateIfDestroyed_alarm_softwareInstanceInvalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'invalidated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      software_instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  def test_tryToInvalidateIfDestroyed_alarm_softwareInstanceMatching(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      software_instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  def test_tryToInvalidateIfDestroyed_alarm_softwareInstanceAllocated(self):
    # This use case is not needed by the alarm
    # But it keeps alarm search way simpler
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      software_instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  def test_tryToInvalidateIfDestroyed_alarm_slaveInstanceAllocated(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      software_instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  #################################################################
  # SoftwareInstance_tryToInvalidateIfDestroyed
  #################################################################
  def test_tryToInvalidateIfDestroyed_REQUEST_disallowed(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.assertRaises(
      Unauthorized,
      software_instance.SoftwareInstance_tryToInvalidateIfDestroyed,
      REQUEST={})

  def test_tryToInvalidateIfDestroyed_script_unexpectedContext(self):
    self.assertRaises(
      TypeError,
      self.portal.SoftwareInstance_tryToInvalidateIfDestroyed,
      )

  def test_tryToInvalidateIfDestroyed_script_expectedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "invalidated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_script_invalidatedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'invalidated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "invalidated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_script_notDestroyedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'stop_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "validated")
    self.assertEqual(software_instance.getSlapState(), "stop_requested")

  def test_tryToInvalidateIfDestroyed_script_allocatedInstance(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "validated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_script_allocatedSlaveInstance(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(project=instance_tree.getFollowUpValue())
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "invalidated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_script_allocatedInstanceOnRemoteNode(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type="Remote Node"
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "validated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_script_allocatedSlaveInstanceOnRemoteNode(self):
    instance_tree = self.addInstanceTree(shared=True)
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type="Remote Node"
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    software_instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(software_instance.getValidationState(), "validated")
    self.assertEqual(software_instance.getSlapState(), "destroy_requested")


class TestSlapOSPropagateRemoteNodeInstance(SlapOSTestCaseMixin):
  launch_caucase = 1

  #################################################################
  # slapos_cloud_propagate_remote_node_instance
  #################################################################
  def test_propagateRemoteNode_alarm_busyPartitionInRemoteNode(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cloud_propagate_remote_node_instance,
      partition,
      'ComputePartition_propagateRemoteNode'
    )

  def test_propagateRemoteNode_alarm_busyPartitionInComputeNode(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue()
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cloud_propagate_remote_node_instance,
      partition,
      'ComputePartition_propagateRemoteNode'
    )

  def test_propagateRemoteNode_alarm_freePartitionInRemoteNode(self):
    instance_tree = self.addInstanceTree()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cloud_propagate_remote_node_instance,
      partition,
      'ComputePartition_propagateRemoteNode'
    )

  #################################################################
  # ComputePartition_propagateRemoteNode
  #################################################################
  def test_propagateRemoteNode_REQUEST_disallowed(self):
    instance_tree = self.addInstanceTree()
    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    self.assertRaises(
      Unauthorized,
      partition.ComputePartition_propagateRemoteNode,
      REQUEST={})

  def test_propagateRemoteNode_script_unexpectedContext(self):
    instance_tree = self.addInstanceTree()
    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue()
    )
    self.assertRaises(
      AssertionError,
      partition.ComputePartition_propagateRemoteNode,
    )

  def test_propagateRemoteNode_script_createRemoteInstanceTree(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    self.assertEqual(remote_instance_tree.getValidationState(), "validated")
    self.assertEqual(remote_instance_tree.getSlapState(), "start_requested")
    self.assertEqual(remote_instance_tree.getUrlString(),
                     software_instance.getUrlString())
    self.assertEqual(remote_instance_tree.getSourceReference(),
                     software_instance.getSourceReference())
    self.assertEqual(remote_instance_tree.getTextContent(),
                     software_instance.getTextContent())
    self.assertEqual(remote_instance_tree.getSlaXml(), None)
    self.assertEqual(remote_instance_tree.isRootSlave(False),
                     software_instance.getPortalType() == 'Slave Instance')

    self.assertEqual(software_instance.getConnectionXml(), None)

  def test_propagateRemoteNode_script_doNotRequestIfNotNeeded(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    remote_modification_date = remote_instance_tree.getModificationDate()

    partition.ComputePartition_propagateRemoteNode()

    self.assertEqual(remote_instance_tree.getModificationDate(),
                     remote_modification_date)

  def test_propagateRemoteNode_script_propageParameterChangesToRemoteInstanceTree(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    remote_modification_date = remote_instance_tree.getModificationDate()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'stop_requested')
    software_instance.edit(
      #url_string=self.generateNewSoftwareReleaseUrl(),
      #source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=self.generateSafeXml()
    )
    partition.ComputePartition_propagateRemoteNode()

    self.assertNotEqual(remote_instance_tree.getModificationDate(),
                        remote_modification_date)
    self.assertEqual(remote_instance_tree.getValidationState(), "validated")
    self.assertEqual(remote_instance_tree.getSlapState(), "stop_requested")
    self.assertEqual(remote_instance_tree.getUrlString(),
                     software_instance.getUrlString())
    self.assertEqual(remote_instance_tree.getSourceReference(),
                     software_instance.getSourceReference())
    self.assertEqual(remote_instance_tree.getTextContent(),
                     software_instance.getTextContent())
    self.assertEqual(remote_instance_tree.getSlaXml(), None)
    self.assertEqual(remote_instance_tree.isRootSlave(False),
                     software_instance.getPortalType() == 'Slave Instance')

    self.assertEqual(software_instance.getConnectionXml(), None)

  def test_propagateRemoteNode_script_propageReleaseChangesToUpgradeDecision(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    remote_software_instance = remote_instance_tree.getSuccessorValue()

    # Create allocated partition to allow Upgrade Decision
    remote_compute_node, remote_partition = self.addComputeNodeAndPartition(
      project=remote_instance_tree.getFollowUpValue(),
    )
    remote_software_instance.setAggregateValue(remote_partition)
    remote_partition.markBusy()

    # Create remote Software Product, to allow generating the Upgrade Decision
    new_id = self.generateNewId()
    software_product = self.portal.software_product_module.newContent(
      reference='TESTSOFTPROD-%s' % new_id,
      title='Test software product %s' % new_id,
      follow_up_value=remote_project
    )
    old_release_variation = software_product.newContent(
      portal_type='Software Product Release Variation',
      url_string=remote_instance_tree.getUrlString()
    )
    type_variation = software_product.newContent(
      portal_type='Software Product Type Variation',
      reference=remote_instance_tree.getSourceReference()
    )
    software_product.publish()
    new_release_variation = self._makeSoftwareRelease(software_product)
    self.addAllocationSupply("old release compute node", remote_compute_node, software_product,
                             old_release_variation, type_variation, disable_alarm=True)
    self.addAllocationSupply("new release compute node", remote_compute_node, software_product,
                             new_release_variation, type_variation, disable_alarm=True)
    self.tic()


    self.portal.portal_workflow._jumpToStateFor(software_instance, 'stop_requested')
    old_release_url = software_instance.getUrlString()
    old_text_content = software_instance.getTextContent()
    software_instance.edit(
      url_string=new_release_variation.getUrlString(),
      text_content=self.generateSafeXml()
    )
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()

    # Instance tree is not modified
    self.assertEqual(remote_instance_tree.getValidationState(), "validated")
    self.assertEqual(remote_instance_tree.getSlapState(), "start_requested")
    self.assertEqual(remote_instance_tree.getUrlString(),
                     old_release_url)
    self.assertEqual(remote_instance_tree.getSourceReference(),
                     software_instance.getSourceReference())
    self.assertEqual(remote_instance_tree.getTextContent(),
                     old_text_content)
    self.assertEqual(remote_instance_tree.getSlaXml(), None)
    self.assertEqual(remote_instance_tree.isRootSlave(False),
                     software_instance.getPortalType() == 'Slave Instance')

    self.assertEqual(software_instance.getConnectionXml(), None)

    self.tic()
    # An upgrade decision is proposed
    upgrade_decision = self.portal.portal_catalog.getResultValue(
      portal_type='Upgrade Decision',
      destination_section__uid=remote_user.getUid(),
      destination_project__uid=remote_project.getUid(),
      aggregate__uid=remote_instance_tree.getUid(),
      resource__uid=software_product.getUid(),
      software_release__uid=new_release_variation.getUid(),
      software_type__uid=type_variation.getUid(),
      simulation_state='confirmed'
    )
    self.assertNotEqual(upgrade_decision, None)

  def test_propagateRemoteNode_script_doNotPropageConnectionXmlIfNotChanged(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    _, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()
    self.tic()

    modification_date = software_instance.getModificationDate()
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()

    self.assertEqual(software_instance.getModificationDate(), modification_date)

  def test_propagateRemoteNode_script_propageConnectionXmlFromRemoteInstanceTree(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )

    modification_date = software_instance.getModificationDate()
    remote_instance = remote_instance_tree.getSuccessorValue()
    remote_instance.edit(
      connection_xml=self.generateSafeXml()
    )
    with TemporaryAlarmScript(self.portal, 'Item_getSubscriptionStatus', "'subscribed'"):
      partition.ComputePartition_propagateRemoteNode()

    self.assertNotEqual(software_instance.getModificationDate(), modification_date)
    self.assertEqual(remote_instance_tree.getValidationState(), "validated")
    self.assertEqual(remote_instance_tree.getSlapState(), "start_requested")
    self.assertEqual(remote_instance_tree.getUrlString(),
                     software_instance.getUrlString())
    self.assertEqual(remote_instance_tree.getSourceReference(),
                     software_instance.getSourceReference())
    self.assertEqual(remote_instance_tree.getTextContent(),
                     software_instance.getTextContent())
    self.assertEqual(remote_instance_tree.getSlaXml(), None)
    self.assertEqual(remote_instance_tree.isRootSlave(False),
                     software_instance.getPortalType() == 'Slave Instance')

    self.assertEqual(software_instance.getConnectionXml(),
                     remote_instance.getConnectionXml())

  def test_propagateRemoteNode_script_propagateDestructionIfValidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    remote_modification_date = remote_instance_tree.getModificationDate()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.tic()
    self.assertEqual(software_instance.getValidationState(), 'validated')
    partition.ComputePartition_propagateRemoteNode()

    self.assertNotEqual(remote_instance_tree.getModificationDate(),
                        remote_modification_date)
    self.assertEqual(remote_instance_tree.getValidationState(), "archived")
    self.assertEqual(remote_instance_tree.getSlapState(), "destroy_requested")
    self.assertEqual(remote_instance_tree.getUrlString(),
                     software_instance.getUrlString())
    self.assertEqual(remote_instance_tree.getSourceReference(),
                     software_instance.getSourceReference())
    self.assertEqual(remote_instance_tree.getTextContent(),
                     software_instance.getTextContent())
    self.assertEqual(remote_instance_tree.getSlaXml(), None)
    self.assertEqual(remote_instance_tree.isRootSlave(False),
                     software_instance.getPortalType() == 'Slave Instance')

    self.assertEqual(software_instance.getConnectionXml(), None)
    self.assertEqual(software_instance.getValidationState(), 'invalidated')

  def test_propagateRemoteNode_script_doNotPropagateDestructionIfInvalidated(self):
    instance_tree = self.addInstanceTree()
    software_instance = instance_tree.getSuccessorValue()

    remote_node, partition = self.addComputeNodeAndPartition(
      project=instance_tree.getFollowUpValue(),
      portal_type='Remote Node'
    )
    software_instance.setAggregateValue(partition)
    partition.markBusy()

    with TemporaryAlarmScript(self.portal, 'ComputePartition_propagateRemoteNode', ""):
      self.tic()

    partition.ComputePartition_propagateRemoteNode()
    self.tic()

    remote_user = remote_node.getDestinationSectionValue()
    remote_project = remote_node.getDestinationProjectValue()
    remote_instance_tree = self.portal.portal_catalog.getResultValue(
      portal_type='Instance Tree',
      destination_section__uid=remote_user.getUid(),
      follow_up__uid=remote_project.getUid(),
      title='_remote_%s_%s' % (software_instance.getFollowUpReference(),
                               software_instance.getReference())
    )
    remote_modification_date = remote_instance_tree.getModificationDate()

    self.portal.portal_workflow._jumpToStateFor(software_instance, 'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance, 'invalidated')
    self.tic()
    partition.ComputePartition_propagateRemoteNode()

    self.assertEqual(remote_instance_tree.getModificationDate(),
                        remote_modification_date)

