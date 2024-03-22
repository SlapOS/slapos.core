# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
import transaction
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from zExceptions import Unauthorized
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate

class TestSlapOSCoreSlapOSAssertInstanceTreeSuccessorAlarm(
    SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

  def test_InstanceTree_assertSuccessor(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

    self.instance_tree.InstanceTree_assertSuccessor()
    self.assertIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_stop_requested(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree,
        'stop_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

    self.instance_tree.InstanceTree_assertSuccessor()
    self.assertIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_destroy_requested(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree,
        'destroy_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

    self.instance_tree.InstanceTree_assertSuccessor()
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

  def test_InstanceTree_assertSuccessor_archived(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.instance_tree.archive()
    self.tic()

    # check that no interaction has recreated the instance
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

    self.instance_tree.InstanceTree_assertSuccessor()
    self.assertNotIn(self.instance_tree.getTitle(),
        self.instance_tree.getSuccessorTitleList())

  def test_alarm_renamed(self):
    self.software_instance.edit(title=self.generateNewSoftwareTitle())
    self._test_alarm(
      self.portal.portal_alarms.slapos_assert_instance_tree_successor,
      self.instance_tree,
      'InstanceTree_assertSuccessor'
    )

  def test_alarm_not_renamed(self):
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_assert_instance_tree_successor,
      self.instance_tree,
      'InstanceTree_assertSuccessor'
    )


class TestSlapOSFreeComputePartitionAlarm(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

  def test_SoftwareInstance_tryToUnallocatePartition(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.tic()
    self.assertEqual(None, self.software_instance.getAggregate())
    self.assertEqual('free', self.partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_concurrency(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.partition.activate(tag="allocate_%s" % self.partition.getRelativeUrl()\
        ).getId()
    transaction.commit()
    self.software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.tic()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate())
    self.assertEqual('busy', self.partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_twoInstances(self):
    software_instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)

    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.tic()
    self.assertEqual(None, self.software_instance.getAggregate())
    self.assertEqual('busy', self.partition.getSlapState())
    self.assertEqual(self.partition.getRelativeUrl(), software_instance.getAggregate())

  def test_alarm_allocated(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.invalidate()

    self._test_alarm(
      self.portal.portal_alarms.slapos_free_compute_partition,
      self.software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_alarm_unallocated(self):
    self._makeComputeNode()
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.invalidate()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      self.software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_alarm_validated(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      self.software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

  def test_alarm_start_requested(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_free_compute_partition,
      self.software_instance,
      'SoftwareInstance_tryToUnallocatePartition'
    )

class TestSlapOSFreeComputePartitionAlarmWithSlave(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree(requested_template_id='template_slave_instance')

  def test_SoftwareInstance_tryToUnallocatePartition(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.tic()
    self.assertEqual(None, self.software_instance.getAggregate())
    self.assertEqual('free', self.partition.getSlapState())

  def test_SoftwareInstance_tryToUnallocatePartition_nonDestroyed(self):
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.tic()

    self.software_instance.SoftwareInstance_tryToUnallocatePartition()
    self.tic()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate())
    self.assertEqual('busy', self.partition.getSlapState())


class TestSlapOSGarbageCollectDestroyedRootTreeAlarm(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

  def test_SoftwareInstance_tryToGarbageCollect(self):
    self.instance_tree.archive()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()
    self.assertEqual('destroy_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_not_destroy_requested(self):
    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()
    self.assertEqual('start_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_not_archived(self):
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()
    self.assertEqual('start_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_only_instance_destroy_requested(self):
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()
    self.assertEqual('start_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_unlinked_successor(self):
    self.requested_software_instance.edit(successor_list=[])
    self.instance_tree.archive()
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()

    self.assertEqual('destroy_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

  def test_SoftwareInstance_tryToGarbageCollect_destroy_unlinked_with_child(self):
    instance_kw = dict(software_release=self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title='Sub Instance',
      state='started'
    )
    self.requested_software_instance.requestInstance(**instance_kw)
    sub_instance = self.requested_software_instance.getSuccessorValue()
    self.assertNotEqual(sub_instance, None)

    self.requested_software_instance.edit(successor_list=[])
    self.instance_tree.archive()
    self.portal.portal_workflow._jumpToStateFor(self.instance_tree,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()

    self.requested_software_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()

    self.assertEqual('destroy_requested',
        self.requested_software_instance.getSlapState())
    self.assertEqual('validated',
        self.requested_software_instance.getValidationState())

    self.assertEqual(self.requested_software_instance.getSuccessorValue(),
                      None)
    self.assertEqual(sub_instance.getSlapState(), 'start_requested')

    sub_instance.SoftwareInstance_tryToGarbageCollect()
    self.tic()

    self.assertEqual(sub_instance.getSlapState(), 'destroy_requested')
    self.assertEqual(sub_instance.getValidationState(), 'validated')

  def test_alarm(self):
    self.instance_tree.archive()
    self._test_alarm(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      self.software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  def test_alarm_invalidated(self):
    self.instance_tree.archive()
    self.software_instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      self.software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )

  def test_alarm_not_archived(self):
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree,
      self.software_instance,
      'SoftwareInstance_tryToGarbageCollect'
    )


class TestSlapOSComputeNode_checkAndUpdateCapacityScope(SlapOSTestCaseMixin):
  allocation_scope_to_test = 'open/public'

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    self.compute_node.edit(
        allocation_scope=self.allocation_scope_to_test,
        reference='TESTC-%s' % self.generateNewId(),
    )
    self.compute_node.edit(capacity_scope='open')
    self.compute_node.validate()
    self.compute_node.setAccessStatus("#access ok")
    transaction.commit()

  def test_ComputeNode_checkAndUpdateCapacityScope(self):
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.compute_node.getCapacityScope())

  def _newComputerModel(self, quantity=None):
    computer_model = self.portal.computer_model_module.\
        template_computer_model.Base_createCloneDocument(batch_mode=1)
    computer_model.edit(capacity_quantity=quantity,
        reference='TESTCM-%s' % self.generateNewId(),
    )
    return computer_model

  def _addPartitionToComputeNode(self):
    partition = self.compute_node.newContent(portal_type='Compute Partition',
        reference='part1')
    partition.markFree()
    partition.markBusy()
    partition.validate()
    self.software_instance.setAggregate(partition.getRelativeUrl())
    self.tic()

  def test_ComputeNode_checkAndUpdateCapacityScope_model(self):
    computer_model = self._newComputerModel(9999)

    self.compute_node.edit(specialise_value=computer_model,
                       capacity_quantity=None)
    transaction.commit()

    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.compute_node.getCapacityScope())
    self.assertEqual(computer_model.getCapacityQuantity(),
                     self.compute_node.getCapacityQuantity())

  def test_ComputeNode_checkAndUpdateCapacityScope_model_no_capacity(self):
    self._makeTree()

    computer_model = self._newComputerModel(1)
    self.compute_node.edit(specialise_value=computer_model,
                       capacity_quantity=None)

    self._addPartitionToComputeNode()
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.compute_node.getCapacityScope())
    self.assertEqual('Compute Node capacity limit exceeded',
        self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual(computer_model.getCapacityQuantity(),
                     self.compute_node.getCapacityQuantity())

  def test_ComputeNode_checkAndUpdateCapacityScope_model_has_capacity(self):
    # If capacity is set on compute_node, model value is ignored.
    self._makeTree()

    computer_model = self._newComputerModel(1)
    self.compute_node.edit(specialise_value=computer_model,
                       capacity_quantity=2)

    self._addPartitionToComputeNode()
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.compute_node.getCapacityScope())

    self.assertNotEqual(computer_model.getCapacityQuantity(),
                     self.compute_node.getCapacityQuantity())

  def test_ComputeNode_checkAndUpdateCapacityScope_with_old_access(self):
    try:
      self.pinDateTime(addToDate(DateTime(),to_add={'minute': -11}))
      self.compute_node.setAccessStatus("#access ok")
    finally:
      self.unpinDateTime()
      
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.compute_node.getCapacityScope())
    self.assertEqual("Compute Node didn't contact for more than 10 minutes",
        self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_no_capacity_quantity(self):
    self._makeTree()
    self.compute_node.edit(capacity_quantity=1)
    self._addPartitionToComputeNode()
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.compute_node.getCapacityScope())
    self.assertEqual('Compute Node capacity limit exceeded',
        self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_no_access(self):
    self.compute_node.edit(reference='TESTC-%s' % self.generateNewId())
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.compute_node.getCapacityScope())
    self.assertEqual("Compute Node didn't contact the server",
        self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

  def test_ComputeNode_checkAndUpdateCapacityScope_close(self):
    self.compute_node.edit(capacity_scope='close')
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.compute_node.getCapacityScope())

  def test_ComputeNode_checkAndUpdateCapacityScope_with_error(self):
    self.compute_node.setAccessStatus('#error not ok')
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.compute_node.getCapacityScope())
    self.assertEqual("Compute Node reported an error",
        self.compute_node.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSComputeNode_checkAndUpdateCapacityScopeSubscription(TestSlapOSComputeNode_checkAndUpdateCapacityScope):
  allocation_scope_to_test = 'open/subscription'

class TestSlapOSComputeNode_checkAndUpdateCapacityScopePersonal(TestSlapOSComputeNode_checkAndUpdateCapacityScope):
  allocation_scope_to_test = 'open/personal'

class TestSlapOSUpdateComputeNodeCapacityScopeAlarm(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    self.compute_node.edit(
        allocation_scope='open/public',
        reference='TESTC-%s' % self.generateNewId(),
    )
    self.compute_node.edit(capacity_scope='open')
    self.compute_node.validate()
    self.compute_node.setAccessStatus("#access ok")
    transaction.commit()

  def test_alarm(self):
    self._test_alarm(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      self.compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

  def test_alarm_subscription(self):
    self.compute_node.edit(allocation_scope='open/subscription')
    self.test_alarm()

  def test_alarm_personal(self):
    self.compute_node.edit(allocation_scope='open/personal')
    self.test_alarm()

  def test_alarm_non_public(self):
    self.compute_node.edit(allocation_scope='close')
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      self.compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

  def test_alarm_invalidated(self):
    self.compute_node.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_update_compute_node_capacity_scope,
      self.compute_node,
      'ComputeNode_checkAndUpdateCapacityScope'
    )

class TestSlapOSGarbageCollectStoppedRootTreeAlarm(SlapOSTestCaseMixin):

  def createInstance(self):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.edit(
    )
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**request_kw)
    instance_tree.requestInstance(**request_kw)

    instance = instance_tree.getSuccessorValue()
    self.tic()
    return instance

  def test_SoftwareInstance_tryToStopCollect_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SoftwareInstance_tryToStopCollect,
      REQUEST={})

  def test_SoftwareInstance_tryToStopCollect_started_instance(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()

    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'stop_requested')
    self.assertEqual('start_requested', instance.getSlapState())

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('stop_requested', instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_destroyed_instance(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()

    self.portal.portal_workflow._jumpToStateFor(instance_tree,
        'stop_requested')
    self.portal.portal_workflow._jumpToStateFor(instance,
        'destroy_requested')

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('destroy_requested', instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_started_subscription(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()

    self.assertEqual('start_requested', instance_tree.getSlapState())
    self.assertEqual('start_requested', instance.getSlapState())

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('start_requested', instance.getSlapState())

  def test_alarm(self):
    instance = self.createInstance()
    self._test_alarm(
      self.portal.portal_alarms.slapos_stop_collect_instance,
      instance,
      'SoftwareInstance_tryToStopCollect'
    )

  def test_alarm_invalidated(self):
    instance = self.createInstance()
    instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_stop_collect_instance,
      instance,
      'SoftwareInstance_tryToStopCollect'
    )

class TestSlapOSGarbageCollectNonAllocatedRootTreeAlarm(SlapOSTestCaseMixin):

  def createInstance(self):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title=instance_tree.getTitle(),
      state='started'
    )
    instance_tree.requestStart(**request_kw)
    instance_tree.requestInstance(**request_kw)

    instance = instance_tree.getSuccessorValue()
    return instance

  def createComputePartition(self):
    compute_node = self.portal.compute_node_module\
        .template_compute_node.Base_createCloneDocument(batch_mode=1)
    compute_node.validate()
    compute_node.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTCOMP-%s" % self.generateNewId(),
    )
    partition = compute_node.newContent(portal_type="Compute Partition")
    return partition

  def test_tryToGarbageCollect_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree,
      REQUEST={})

  def test_tryToGarbageCollect_invalidated_instance(self):
    instance = self.createInstance()
    instance.invalidate()
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_destroyed_instance(self):
    instance = self.createInstance()
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_allocated_instance(self):
    instance = self.createInstance()
    partition = self.createComputePartition()
    instance.edit(aggregate_value=partition)
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_no_allocation_try_found(self):
    instance = self.createInstance()
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_recent_allocation_try_found(self):
    instance = self.createInstance()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())


  def test_tryToGarbageCollect_recent_allocation_try_found_allocation_disallowed(self):
    instance = self.createInstance()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    instance_tree = instance.getSpecialiseValue()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_complex_tree(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()
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
    instance.requestInstance(**request_kw)
    sub_instance = instance.getSuccessorValue()
    self.tic()
    sub_instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    })

    sub_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_complex_tree_allocation_disallowed(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()
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
    instance.requestInstance(**request_kw)
    sub_instance = instance.getSuccessorValue()
    self.tic()
    sub_instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    })

    sub_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance_tree.getSlapState())

  def test_tryToGarbageCollect_old_allocation_try_found(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Compute Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -8}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance_tree.getSlapState())
    self.assertEqual('archived', instance_tree.getValidationState())


  def test_tryToGarbageCollect_old_allocation_try_found_allocation_disallowed(self):
    instance = self.createInstance()
    instance_tree = instance.getSpecialiseValue()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: Allocation disallowed',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -8}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance_tree.getSlapState())
    self.assertEqual('archived', instance_tree.getValidationState())

  def test_alarm(self):
    instance = self.createInstance()
    self._test_alarm(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )

  def test_alarm_invalidated(self):
    instance = self.createInstance()
    instance.invalidate()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )

  def test_alarm_allocated(self):
    instance = self.createInstance()
    partition = self.createComputePartition()
    instance.edit(aggregate_value=partition)
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree,
      instance,
      'SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree'
    )


class TestSlapOSInvalidateDestroyedInstance(SlapOSTestCaseMixin):

  def createSoftwareInstance(self):
    new_id = self.generateNewId()
    return self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title="Test instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      )

  def createComputePartition(self):
    new_id = self.generateNewId()
    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title="Test compute_node %s" % new_id,
      reference="TESTCOMP-%s" % new_id,
      )
    compute_partition = compute_node.newContent(
      portal_type='Compute Partition',
      )
    return compute_partition

  def test_tryToInvalidateIfDestroyed_REQUEST_disallowed(self):
    instance = self.createSoftwareInstance()
    self.assertRaises(
      Unauthorized,
      instance.SoftwareInstance_tryToInvalidateIfDestroyed,
      REQUEST={})

  def test_tryToInvalidateIfDestroyed_unexpected_context(self):
    self.assertRaises(
      TypeError,
      self.portal.SoftwareInstance_tryToInvalidateIfDestroyed,
      )

  def test_tryToInvalidateIfDestroyed_expected_instance(self):
    instance = self.createSoftwareInstance()
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(instance.getValidationState(), "invalidated")
    self.assertEqual(instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_invalidated_instance(self):
    instance = self.createSoftwareInstance()
    self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(instance.getValidationState(), "invalidated")
    self.assertEqual(instance.getSlapState(), "destroy_requested")

  def test_tryToInvalidateIfDestroyed_not_destroyed_instance(self):
    instance = self.createSoftwareInstance()
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'stop_requested')
    instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(instance.getValidationState(), "validated")
    self.assertEqual(instance.getSlapState(), "stop_requested")

  def test_tryToInvalidateIfDestroyed_allocated_instance(self):
    instance = self.createSoftwareInstance()
    partition = self.createComputePartition()
    instance.edit(aggregate_value=partition)
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(instance.getValidationState(), "validated")
    self.assertEqual(instance.getSlapState(), "destroy_requested")

  def test_alarm_software_instance_allocated(self):
    instance = self.createSoftwareInstance()
    partition = self.createComputePartition()
    instance.edit(aggregate_value=partition)
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  def test_alarm_software_instance_invalidated(self):
    instance = self.createSoftwareInstance()
    self.createComputePartition()
    self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )

  def test_alarm_software_instance_matching(self):
    instance = self.createSoftwareInstance()
    self.createComputePartition()
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance,
      instance,
      'SoftwareInstance_tryToInvalidateIfDestroyed'
    )
