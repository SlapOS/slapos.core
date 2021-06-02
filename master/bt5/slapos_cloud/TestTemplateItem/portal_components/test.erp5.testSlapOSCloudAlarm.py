# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
import transaction
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from Products.ERP5Type.tests.utils import createZODBPythonScript
import json
import time
from zExceptions import Unauthorized
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate
from App.Common import rfc1123_date

class TestSlapOSCoreSlapOSAssertHostingSubscriptionSuccessorAlarm(
    SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

  def test_HostingSubscription_assertSuccessor(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.tic()

    # check that no interaction has recreated the instance
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

    self.hosting_subscription.HostingSubscription_assertSuccessor()
    self.assertTrue(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

  def test_HostingSubscription_assertSuccessor_stop_requested(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription,
        'stop_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

    self.hosting_subscription.HostingSubscription_assertSuccessor()
    self.assertTrue(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

  def test_HostingSubscription_assertSuccessor_destroy_requested(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription,
        'destroy_requested')
    self.tic()

    # check that no interaction has recreated the instance
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

    self.hosting_subscription.HostingSubscription_assertSuccessor()
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

  def test_HostingSubscription_assertSuccessor_archived(self):
    self.software_instance.rename(new_name=self.generateNewSoftwareTitle())
    self.hosting_subscription.archive()
    self.tic()

    # check that no interaction has recreated the instance
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

    self.hosting_subscription.HostingSubscription_assertSuccessor()
    self.assertFalse(self.hosting_subscription.getTitle() in
        self.hosting_subscription.getSuccessorTitleList())

  def _simulateHostingSubscription_assertSuccessor(self):
    script_name = 'HostingSubscription_assertSuccessor'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by HostingSubscription_assertSuccessor') """ )
    transaction.commit()

  def _dropHostingSubscription_assertSuccessor(self):
    script_name = 'HostingSubscription_assertSuccessor'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_alarm_renamed(self):
    self.software_instance.edit(title=self.generateNewSoftwareTitle())
    self.tic()
    self._simulateHostingSubscription_assertSuccessor()
    try:
      self.portal.portal_alarms.slapos_assert_hosting_subscription_successor.activeSense()
      self.tic()
    finally:
      self._dropHostingSubscription_assertSuccessor()
    self.assertEqual(
        'Visited by HostingSubscription_assertSuccessor',
        self.hosting_subscription.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_renamed(self):
    self._simulateHostingSubscription_assertSuccessor()
    try:
      self.portal.portal_alarms.slapos_assert_hosting_subscription_successor.activeSense()
      self.tic()
    finally:
      self._dropHostingSubscription_assertSuccessor()
    self.assertNotEqual(
        'Visited by HostingSubscription_assertSuccessor',
        self.hosting_subscription.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSFreeComputerPartitionAlarm(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree()

  def test_SoftwareInstance_tryToUnallocatePartition(self):
    self._makeComputer()
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
    self._makeComputer()
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

    self._makeComputer()
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
    self._makeComputer()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.invalidate()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToUnallocatePartition')
    try:
      self.portal.portal_alarms.slapos_free_computer_partition.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToUnallocatePartition')
    self.assertEqual(
        'Visited by SoftwareInstance_tryToUnallocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_unallocated(self):
    self._makeComputer()
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.software_instance.invalidate()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToUnallocatePartition')
    try:
      self.portal.portal_alarms.slapos_free_computer_partition.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToUnallocatePartition')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToUnallocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_validated(self):
    self._makeComputer()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.portal.portal_workflow._jumpToStateFor(self.software_instance,
        'destroy_requested')
    self.tic()
    self._simulateScript('SoftwareInstance_tryToUnallocatePartition')
    try:
      self.portal.portal_alarms.slapos_free_computer_partition.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToUnallocatePartition')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToUnallocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_start_requested(self):
    self._makeComputer()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.partition.markBusy()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToUnallocatePartition')
    try:
      self.portal.portal_alarms.slapos_free_computer_partition.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToUnallocatePartition')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToUnallocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSFreeComputerPartitionAlarmWithSlave(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self._makeTree(requested_template_id='template_slave_instance')

  def test_SoftwareInstance_tryToUnallocatePartition(self):
    self._makeComputer()
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
    self._makeComputer()
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
    self.hosting_subscription.archive()
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
    self.hosting_subscription.archive()
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription,
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
    self.hosting_subscription.archive()
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription,
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

  def _simulateSoftwareInstance_tryToGarbageCollect(self):
    script_name = 'SoftwareInstance_tryToGarbageCollect'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SoftwareInstance_tryToGarbageCollect') """ )
    transaction.commit()

  def _dropSoftwareInstance_tryToGarbageCollect(self):
    script_name = 'SoftwareInstance_tryToGarbageCollect'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_alarm(self):
    self.hosting_subscription.archive()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToGarbageCollect')
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollect')
    self.assertEqual(
        'Visited by SoftwareInstance_tryToGarbageCollect',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_invalidated(self):
    self.hosting_subscription.archive()
    self.software_instance.invalidate()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToGarbageCollect')
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollect')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToGarbageCollect',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_not_archived(self):
    self.tic()
    self._simulateScript('SoftwareInstance_tryToGarbageCollect')
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroyed_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollect')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToGarbageCollect',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSUpdateComputerCapacityScopeAlarm(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.computer = self.portal.computer_module.template_computer\
        .Base_createCloneDocument(batch_mode=1)
    self.computer.edit(
        allocation_scope='open/public',
        reference='TESTC-%s' % self.generateNewId(),
    )
    self.computer.edit(capacity_scope='open')
    self.computer.validate()
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')
    memcached_dict[self.computer.getReference()] = json.dumps({
        'text': '#access ok',
        'created_at': rfc1123_date(DateTime())
    })
    transaction.commit()

  def test_Computer_checkAndUpdateCapacityScope(self):
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.computer.getCapacityScope())

  def _newComputerModel(self, quantity=None):
    computer_model = self.portal.computer_model_module.\
        template_computer_model.Base_createCloneDocument(batch_mode=1)
    computer_model.edit(capacity_quantity=quantity,
        reference='TESTCM-%s' % self.generateNewId(),
    )
    return computer_model

  def _addPartitionToComputer(self):
    partition = self.computer.newContent(portal_type='Computer Partition',
        reference='part1')
    partition.markFree()
    partition.markBusy()
    partition.validate()
    self.software_instance.setAggregate(partition.getRelativeUrl())
    self.tic()

  def test_Computer_checkAndUpdateCapacityScope_model(self):
    computer_model = self._newComputerModel(9999)

    self.computer.edit(specialise_value=computer_model,
                       capacity_quantity=None)
    transaction.commit()

    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.computer.getCapacityScope())
    self.assertEqual(computer_model.getCapacityQuantity(),
                     self.computer.getCapacityQuantity())

  def test_Computer_checkAndUpdateCapacityScope_model_no_capacity(self):
    self._makeTree()

    computer_model = self._newComputerModel(1)
    self.computer.edit(specialise_value=computer_model,
                       capacity_quantity=None)

    self._addPartitionToComputer()
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.computer.getCapacityScope())
    self.assertEqual('Computer capacity limit exceeded',
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

    self.assertEqual(computer_model.getCapacityQuantity(),
                     self.computer.getCapacityQuantity())

  def test_Computer_checkAndUpdateCapacityScope_model_has_capacity(self):
    # If capacity is set on computer, model value is ignored.
    self._makeTree()

    computer_model = self._newComputerModel(1)
    self.computer.edit(specialise_value=computer_model,
                       capacity_quantity=2)

    self._addPartitionToComputer()
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.computer.getCapacityScope())

    self.assertNotEqual(computer_model.getCapacityQuantity(),
                     self.computer.getCapacityQuantity())

  def test_Computer_checkAndUpdateCapacityScope_with_old_access(self):
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')
    memcached_dict[self.computer.getReference()] = json.dumps({
        'text': '#access ok',
        'created_at': rfc1123_date(addToDate(DateTime(),
                                             to_add={'minute': -11}))
    })
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.computer.getCapacityScope())
    self.assertEqual("Computer didn't contact for more than 10 minutes",
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_Computer_checkAndUpdateCapacityScope_no_capacity_quantity(self):
    self._makeTree()
    self.computer.edit(capacity_quantity=1)
    self._addPartitionToComputer()
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.computer.getCapacityScope())
    self.assertEqual('Computer capacity limit exceeded',
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_Computer_checkAndUpdateCapacityScope_no_access(self):
    self.computer.edit(reference='TESTC-%s' % self.generateNewId())
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.computer.getCapacityScope())
    self.assertEqual("Computer didn't contact the server",
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_Computer_checkAndUpdateCapacityScope_close(self):
    self.computer.edit(capacity_scope='close')
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.computer.getCapacityScope())

  def test_Computer_checkAndUpdateCapacityScope_with_error(self):
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')
    memcached_dict[self.computer.getReference()] = json.dumps({
        'text': '#error not ok'
    })
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('close', self.computer.getCapacityScope())
    self.assertEqual("Computer reported an error",
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_Computer_checkAndUpdateCapacityScope_with_error_non_public(self):
    memcached_dict = self.portal.portal_memcached.getMemcachedDict(
        key_prefix='slap_tool',
        plugin_path='portal_memcached/default_memcached_plugin')
    memcached_dict[self.computer.getReference()] = json.dumps({
        'text': '#error not ok'
    })
    self.computer.edit(allocation_scope='open/personal')
    self.computer.Computer_checkAndUpdateCapacityScope()
    self.assertEqual('open', self.computer.getCapacityScope())

  def _simulateComputer_checkAndUpdateCapacityScope(self):
    script_name = 'Computer_checkAndUpdateCapacityScope'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by Computer_checkAndUpdateCapacityScope') """ )
    transaction.commit()

  def _dropComputer_checkAndUpdateCapacityScope(self):
    script_name = 'Computer_checkAndUpdateCapacityScope'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_alarm(self):
    self.tic()
    self._simulateComputer_checkAndUpdateCapacityScope()
    try:
      self.portal.portal_alarms.slapos_update_computer_capacity_scope.activeSense()
      self.tic()
    finally:
      self._dropComputer_checkAndUpdateCapacityScope()
    self.assertEqual(
        'Visited by Computer_checkAndUpdateCapacityScope',
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_non_public(self):
    self.computer.edit(allocation_scope='open/personal')
    self.tic()
    self._simulateComputer_checkAndUpdateCapacityScope()
    try:
      self.portal.portal_alarms.slapos_update_computer_capacity_scope.activeSense()
      self.tic()
    finally:
      self._dropComputer_checkAndUpdateCapacityScope()
    self.assertNotEqual(
        'Visited by Computer_checkAndUpdateCapacityScope',
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_invalidated(self):
    self.computer.invalidate()
    self.tic()
    self._simulateComputer_checkAndUpdateCapacityScope()
    try:
      self.portal.portal_alarms.slapos_update_computer_capacity_scope.activeSense()
      self.tic()
    finally:
      self._dropComputer_checkAndUpdateCapacityScope()
    self.assertNotEqual(
        'Visited by Computer_checkAndUpdateCapacityScope',
        self.computer.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSGarbageCollectStoppedRootTreeAlarm(SlapOSTestCaseMixin):

  def createInstance(self):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.edit(
    )
    hosting_subscription.validate()
    hosting_subscription.edit(
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
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**request_kw)
    hosting_subscription.requestInstance(**request_kw)

    instance = hosting_subscription.getSuccessorValue()
    self.tic()
    return instance

  def test_SoftwareInstance_tryToStopCollect_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.SoftwareInstance_tryToStopCollect,
      REQUEST={})

  def test_SoftwareInstance_tryToStopCollect_started_instance(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()

    self.portal.portal_workflow._jumpToStateFor(hosting_subscription,
        'stop_requested')
    self.assertEqual('start_requested', instance.getSlapState())

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('stop_requested', instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_destroyed_instance(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()

    self.portal.portal_workflow._jumpToStateFor(hosting_subscription,
        'stop_requested')
    self.portal.portal_workflow._jumpToStateFor(instance,
        'destroy_requested')

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('destroy_requested', instance.getSlapState())

  def test_SoftwareInstance_tryToStopCollect_started_subscription(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()

    self.assertEqual('start_requested', hosting_subscription.getSlapState())
    self.assertEqual('start_requested', instance.getSlapState())

    instance.SoftwareInstance_tryToStopCollect()
    self.assertEqual('start_requested', instance.getSlapState())

  def test_alarm(self):
    instance = self.createInstance()
    self._simulateScript('SoftwareInstance_tryToStopCollect')
    try:
      self.portal.portal_alarms.slapos_stop_collect_instance.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToStopCollect')
    self.assertEqual(
        'Visited by SoftwareInstance_tryToStopCollect',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_invalidated(self):
    instance = self.createInstance()
    instance.invalidate()
    self.tic()
    self._simulateScript('SoftwareInstance_tryToStopCollect')
    try:
      self.portal.portal_alarms.slapos_stop_collect_instance.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToStopCollect')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToStopCollect',
        instance.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSGarbageCollectNonAllocatedRootTreeAlarm(SlapOSTestCaseMixin):

  def createInstance(self):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    hosting_subscription.edit(
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
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**request_kw)
    hosting_subscription.requestInstance(**request_kw)

    instance = hosting_subscription.getSuccessorValue()
    return instance

  def createComputerPartition(self):
    computer = self.portal.computer_module\
        .template_computer.Base_createCloneDocument(batch_mode=1)
    computer.validate()
    computer.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTCOMP-%s" % self.generateNewId(),
    )
    partition = computer.newContent(portal_type="Computer Partition")
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
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_destroyed_instance(self):
    instance = self.createInstance()
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', instance.getSlapState())
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_allocated_instance(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_no_allocation_try_found(self):
    instance = self.createInstance()
    self.tic()

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_recent_allocation_try_found(self):
    instance = self.createInstance()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Computer Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -2}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', instance.getSlapState())
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())


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
    hosting_subscription = instance.getSpecialiseValue()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_complex_tree(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title="another %s" % hosting_subscription.getTitle(),
      state='started'
    )
    instance.requestInstance(**request_kw)
    sub_instance = instance.getSuccessorValue()
    self.tic()
    sub_instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Computer Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -4}),
        'action': 'edit'
    })

    sub_instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_complex_tree_allocation_disallowed(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()
    request_kw = dict(
      software_release=\
          self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=False,
      software_title="another %s" % hosting_subscription.getTitle(),
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
    self.assertEqual('start_requested', hosting_subscription.getSlapState())

  def test_tryToGarbageCollect_old_allocation_try_found(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()
    self.tic()
    instance.workflow_history['edit_workflow'].append({
        'comment':'Allocation failed: no free Computer Partition',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': '',
        'time': addToDate(DateTime(), to_add={'day': -8}),
        'action': 'edit'
    })

    instance.SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree()
    self.assertEqual('destroy_requested', hosting_subscription.getSlapState())
    self.assertEqual('archived', hosting_subscription.getValidationState())


  def test_tryToGarbageCollect_old_allocation_try_found_allocation_disallowed(self):
    instance = self.createInstance()
    hosting_subscription = instance.getSpecialiseValue()
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
    self.assertEqual('destroy_requested', hosting_subscription.getSlapState())
    self.assertEqual('archived', hosting_subscription.getValidationState())

  def test_alarm(self):
    instance = self.createInstance()
    self.tic()
    self._simulateScript("SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree")
    try:
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree')
    self.assertEqual(
        'Visited by SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_invalidated(self):
    instance = self.createInstance()
    instance.invalidate()
    self.tic()
    self._simulateScript("SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree")
    try:
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_allocated(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    self._simulateScript("SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree")
    try:
      self.portal.portal_alarms.slapos_garbage_collect_non_allocated_root_tree.activeSense()
      self.tic()
    finally:
      self._dropScript('SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree')
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToGarbageCollectNonAllocatedRootTree',
        instance.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSGarbageCollectUnlinkedInstanceAlarm(SlapOSTestCaseMixin):

  def createInstance(self):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    hosting_subscription.edit(
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
      software_title=hosting_subscription.getTitle(),
      state='started'
    )
    hosting_subscription.requestStart(**request_kw)
    hosting_subscription.requestInstance(**request_kw)
    self.hosting_subscription = hosting_subscription

    instance = hosting_subscription.getSuccessorValue()
    return instance

  def createComputerPartition(self):
    computer = self.portal.computer_module\
        .template_computer.Base_createCloneDocument(batch_mode=1)
    computer.validate()
    computer.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTCOMP-%s" % self.generateNewId(),
    )
    partition = computer.newContent(portal_type="Computer Partition")
    return partition

  def doRequestInstance(self, instance, title, slave=False):
    instance_kw = dict(software_release=self.generateNewSoftwareReleaseUrl(),
      software_type=self.generateNewSoftwareType(),
      instance_xml=self.generateSafeXml(),
      sla_xml=self.generateSafeXml(),
      shared=slave,
      software_title=title,
      state='started'
    )
    instance.requestInstance(**instance_kw)
    self.tic()
    sub_instance = instance.getSuccessorValue()
    partition = self.createComputerPartition()
    sub_instance.edit(aggregate_value=partition)
    self.tic()
    self.assertEqual(self.hosting_subscription.getRelativeUrl(),
                    sub_instance.getSpecialise())  
    return sub_instance

  def _simulateSoftwareInstance_tryToGarbageUnlinkedInstance(self):
    script_name = 'SoftwareInstance_tryToGarbageUnlinkedInstance'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SoftwareInstance_tryToGarbageUnlinkedInstance') """ )
    transaction.commit()

  def _dropSoftwareInstance_tryToGarbageUnlinkedInstance(self):
    script_name = 'SoftwareInstance_tryToGarbageUnlinkedInstance'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    self.assertEqual(instance0.getSuccessorRelatedTitle(), instance.getTitle())

    # Remove successor link
    instance.edit(successor_list=[])
    self.tic()
    self.assertEqual(instance0.getSuccessorRelatedTitle(), None)
    instance0.SoftwareInstance_tryToGarbageUnlinkedInstance(delay_time=-1)
    self.tic()
    self.assertEqual(instance0.getSlapState(), 'destroy_requested')

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance_hosting_destroyed(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    instance.edit(successor_list=[])
    self.tic()

    self.hosting_subscription.archive()
    self.portal.portal_workflow._jumpToStateFor(self.hosting_subscription,
        'destroy_requested')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    instance0.SoftwareInstance_tryToGarbageUnlinkedInstance()
    self.tic()
    # Will not be destroyed by this script
    self.assertEqual(instance0.getSlapState(), 'start_requested')

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance_will_unlink_children(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    instance_instance0 = self.doRequestInstance(instance0, 'Subinstance0')
    self.assertEqual(instance_instance0.getSuccessorRelatedTitle(),
                     'instance0')
    instance.edit(successor_list=[])
    self.tic()
    self.assertEqual(instance0.getSuccessorRelatedTitle(), None)

    instance0.SoftwareInstance_tryToGarbageUnlinkedInstance(delay_time=-1)
    self.tic()
    self.assertEqual(instance0.getSlapState(), 'destroy_requested')
    self.assertEqual(instance_instance0.getSlapState(), 'start_requested')
    # Link of child removed
    self.assertEqual(instance_instance0.getSuccessorRelatedTitle(), None)

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance_will_delay(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    instance_instance0 = self.doRequestInstance(instance0, 'Subinstance0')
    self.assertEqual(instance_instance0.getSuccessorRelatedTitle(),
                     'instance0')
    instance.edit(successor_list=[])
    self.tic()
    self.assertEqual(instance0.getSuccessorRelatedTitle(), None)

    instance0.SoftwareInstance_tryToGarbageUnlinkedInstance()
    self.tic()
    self.assertEqual(instance0.getSlapState(), 'start_requested')
    self.assertEqual(instance_instance0.getSlapState(), 'start_requested')

    # delay a bit
    time.sleep(2)
    # run with delay of 3 seconds
    instance0.SoftwareInstance_tryToGarbageUnlinkedInstance(delay_time=3/60.0)
    self.tic()

    self.assertEqual(instance0.getSlapState(), 'destroy_requested')
    self.assertEqual(instance_instance0.getSlapState(), 'start_requested')
    # Link of child removed
    self.assertEqual(instance_instance0.getSuccessorRelatedTitle(), None)

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance_unlinked_root(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()

    self.assertEqual(self.hosting_subscription.getTitle(), instance.getTitle())

    # Remove successor link
    self.hosting_subscription.edit(successor_list=[])
    self.tic()
    self.assertEqual(instance.getSuccessorRelatedTitle(), None)
    # will not destroy
    self.assertRaises(
      ValueError,
      instance.SoftwareInstance_tryToGarbageUnlinkedInstance,
      delay_time=-10)
    self.tic()
    self.assertEqual(instance.getSlapState(), 'start_requested')

  def test_SoftwareInstance_tryToGarbageUnlinkedInstance_not_unlinked(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    instance_instance0 = self.doRequestInstance(instance0, 'Subinstance0')
    self.assertEqual(instance_instance0.getSuccessorRelatedTitle(),
                     'instance0')
    self.assertEqual(instance_instance0.getSlapState(), 'start_requested')

    # Try to remove without delete successor link
    instance_instance0.SoftwareInstance_tryToGarbageUnlinkedInstance(delay_time=-1)
    self.tic()
    self.assertEqual(instance_instance0.getSlapState(), 'start_requested')

  def test_alarm_search_inlinked_instance(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    instance0 = self.doRequestInstance(instance, 'instance0')
    self.assertEqual(instance.getSuccessorReference(),
                      instance0.getReference())
    self._simulateSoftwareInstance_tryToGarbageUnlinkedInstance()
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroy_unlinked_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToGarbageUnlinkedInstance()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToGarbageUnlinkedInstance',
        instance0.workflow_history['edit_workflow'][-1]['comment'])

    # Remove successor link
    instance.edit(successor_list=[])
    self._simulateSoftwareInstance_tryToGarbageUnlinkedInstance()
    self.tic()
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroy_unlinked_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToGarbageUnlinkedInstance()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToGarbageUnlinkedInstance',
        instance0.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_search_inlinked_instance_slave(self):
    instance = self.createInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.tic()
    slave_instance0 = self.doRequestInstance(instance, 'slaveInstance0', True)
    self.assertEqual(instance.getSuccessorTitle(), 'slaveInstance0')
    self._simulateSoftwareInstance_tryToGarbageUnlinkedInstance()
    instance.edit(successor_list=[])
    self.tic()
    try:
      self.portal.portal_alarms.slapos_garbage_collect_destroy_unlinked_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToGarbageUnlinkedInstance()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToGarbageUnlinkedInstance',
        slave_instance0.workflow_history['edit_workflow'][-1]['comment'])

class TestSlapOSInvalidateDestroyedInstance(SlapOSTestCaseMixin):

  def createSoftwareInstance(self):
    new_id = self.generateNewId()
    return self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      title="Test instance %s" % new_id,
      reference="TESTINST-%s" % new_id,
      )

  def createComputerPartition(self):
    new_id = self.generateNewId()
    computer = self.portal.computer_module.newContent(
      portal_type='Computer',
      title="Test computer %s" % new_id,
      reference="TESTCOMP-%s" % new_id,
      )
    computer_partition = computer.newContent(
      portal_type='Computer Partition',
      )
    return computer_partition

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
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    instance.SoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(instance.getValidationState(), "validated")
    self.assertEqual(instance.getSlapState(), "destroy_requested")

  def _simulateSoftwareInstance_tryToInvalidateIfDestroyed(self):
    script_name = 'SoftwareInstance_tryToInvalidateIfDestroyed'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SoftwareInstance_tryToInvalidateIfDestroyed') """ )
    transaction.commit()

  def _dropSoftwareInstance_tryToInvalidateIfDestroyed(self):
    script_name = 'SoftwareInstance_tryToInvalidateIfDestroyed'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_alarm_software_instance_allocated(self):
    instance = self.createSoftwareInstance()
    partition = self.createComputerPartition()
    instance.edit(aggregate_value=partition)
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._simulateSoftwareInstance_tryToInvalidateIfDestroyed()
    try:
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance.\
          activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToInvalidateIfDestroyed',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_software_instance_invalidated(self):
    instance = self.createSoftwareInstance()
    self.createComputerPartition()
    self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._simulateSoftwareInstance_tryToInvalidateIfDestroyed()
    try:
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance.\
          activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToInvalidateIfDestroyed',
        instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_software_instance_matching(self):
    instance = self.createSoftwareInstance()
    self.createComputerPartition()
    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    self.portal.portal_workflow._jumpToStateFor(instance, 'destroy_requested')
    self.tic()

    self._simulateSoftwareInstance_tryToInvalidateIfDestroyed()
    try:
      self.portal.portal_alarms.slapos_cloud_invalidate_destroyed_instance.\
          activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToInvalidateIfDestroyed()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToInvalidateIfDestroyed',
        instance.workflow_history['edit_workflow'][-1]['comment'])
