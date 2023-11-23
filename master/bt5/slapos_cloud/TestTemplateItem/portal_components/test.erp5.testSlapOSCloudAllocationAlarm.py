# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
import transaction
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, simulate
from Products.ERP5Type.tests.utils import createZODBPythonScript
from unittest import skip


class TestSlapOSAllocation(SlapOSTestCaseMixin):

  def _makeSlaveTree(self, requested_template_id='template_slave_instance'):
    SlapOSTestCaseMixin._makeTree(self, requested_template_id=requested_template_id)

  def _simulatePerson_isAllowedToAllocate(self):
    script_name = 'Person_isAllowedToAllocate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by Person_isAllowedToAllocate')
return True""" )
    transaction.commit()

  def _simulatePerson_isNotAllowedToAllocate(self):
    script_name = 'Person_isAllowedToAllocate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""return False""")
    transaction.commit()

  def _dropPerson_isAllowedToAllocate(self):
    script_name = 'Person_isAllowedToAllocate'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  def test_person_allocation_checked(self):
    self._makeTree()
    self._simulatePerson_isAllowedToAllocate()
    try:
      self.software_instance.SoftwareInstance_tryToAllocatePartition()
    finally:
      self._dropPerson_isAllowedToAllocate()
    self.assertEqual(
        'Visited by Person_isAllowedToAllocate',
        self.person_user.workflow_history['edit_workflow'][-1]['comment'])

  def test_no_allocation_if_person_is_not_allowed(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self._simulatePerson_isNotAllowedToAllocate()
    try:
      self.software_instance.SoftwareInstance_tryToAllocatePartition()
    finally:
      self._dropPerson_isAllowedToAllocate()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.assertEqual(
        'Allocation failed: Allocation disallowed',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_no_free_partition(self):
    self._makeTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_no_host_instance(self):
    self._makeSlaveTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

  def _installSoftware(self, compute_node, url):
    software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    software_installation.edit(url_string=url,
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        aggregate=compute_node.getRelativeUrl())
    software_installation.validate()
    software_installation.requestStart()
    self.tic()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_free_partition(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  def _allocateHost(self, software_instance, compute_partition):
    software_instance.edit(
        aggregate_value=compute_partition
        )
    compute_partition.markBusy()
    self.tic()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_instance(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_capacity_scope_close(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())
    self.compute_node.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_capacity_scope_close(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.compute_node.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_allocation_scope_close(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())
    self.compute_node.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_allocation_scope_close(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.compute_node.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_allocation_scope_open_personal(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())
    self.compute_node.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.compute_node.setAccessStatus("#access ok")
    self.tic()
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual(self.compute_node.getCapacityScope(), 'open')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_allocation_scope_open_personal(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.compute_node.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.compute_node.setAccessStatus("#access ok")
    self.tic()
    self.compute_node.ComputeNode_checkAndUpdateCapacityScope()
    self.assertEqual(self.compute_node.getCapacityScope(), 'open')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_does_not_fail_on_instance_with_damaged_sla_xml(self):
    self._makeTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    transaction.abort()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_does_not_fail_on_slave_with_damaged_sla_xml(self):
    self._makeSlaveTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    transaction.abort()

  def _simulateSoftwareInstance_tryToAllocatePartition(self):
    script_name = 'SoftwareInstance_tryToAllocatePartition'
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        '*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
portal_workflow.doActionFor(context, action='edit_action', comment='Visited by SoftwareInstance_tryToAllocatePartition') """ )
    transaction.commit()

  def _dropSoftwareInstance_tryToAllocatePartition(self):
    script_name = 'SoftwareInstance_tryToAllocatePartition'
    if script_name in self.portal.portal_skins.custom.objectIds():
      self.portal.portal_skins.custom.manage_delObjects(script_name)
    transaction.commit()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_alarm_software_instance_unallocated(self):
    self._makeTree()

    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_alarm_slave_instance_unallocated(self):
    self._makeSlaveTree()

    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_alarm_software_instance_allocated(self):
    self._makeTree()

    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()
    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_alarm_slave_instance_allocated(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()
    self._simulateSoftwareInstance_tryToAllocatePartition()
    try:
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()
    finally:
      self._dropSoftwareInstance_tryToAllocatePartition()
    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_computer_guid(self):
    self._makeTree()

    self._makeComputeNode()
    self.assertEqual(self.compute_node.getAllocationScope(), "open/public")
    self.assertEqual(self.compute_node.getCapacityScope(), "open")

    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s_foo' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_instance_guid(self):
    self._makeSlaveTree()

    self._makeComputeNode()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_network_guid(self):
    self._makeTree()

    self._makeComputeNode()
    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    self.compute_node.edit(
        subordination_value=computer_network)
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_one_network(self):
    """
    Test that when mode is "unique_by_network", we deploy new instance on
    compute_node network not already used by any software instance of the
    instance tree.
    Then test that we do NOT deploy new instance on
    compute_node network already used by any software instance of the
    instance tree.
    """
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    compute_node1 = self._makeComputeNode()[0]
    compute_node2 = self._makeComputeNode()[0]
    self._installSoftware(compute_node1, self.software_instance.getUrlString())
    self._installSoftware(compute_node2, self.software_instance.getUrlString())

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    compute_node1.edit(subordination_value=computer_network)
    compute_node2.edit(subordination_value=computer_network)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance2 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.instance_tree.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    self.tic()

    self.assertEqual(None,
      self.software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(self.software_instance.getSlapState(), 'start_requested')
    self.assertEqual(self.software_instance.getValidationState(), 'validated')

    self.software_instance.setSlaXml(sla_xml)
    self.software_instance.SoftwareInstance_tryToAllocatePartition()

    self.tic()
    portal_workflow = self.software_instance.portal_workflow
    last_workflow_item = portal_workflow.getInfoFor(ob=self.software_instance,
                                          name='comment', wf_id='edit_workflow')
    self.assertEqual(None,last_workflow_item)
    self.assertNotEqual(None,
      self.software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(
        computer_network.getReference(),
        self.software_instance.getAggregateValue(portal_type='Compute Partition')\
            .getParentValue().getSubordinationReference(),
    )

    self.tic()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Compute Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_several_network(self):
    """
    Test that when mode is "unique_by_network", we deploy new instance on
    compute_node network not already used by any software instance of the
    instance tree.
    Then test that we do NOT deploy new instance on
    compute_node network already used by any software instance of the
    instance tree.
    Test with 3 instances and 3 existing compute_nodes on 2 different networks.
    """
    self.tic()
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    compute_node1, partition1 = self._makeComputeNode()
    compute_node2 = self._makeComputeNode()[0]
    compute_node3, partition3 = self._makeComputeNode()
    computer_network1 = self._makeComputerNetwork()
    computer_network2 = self._makeComputerNetwork()

    compute_node1.edit(subordination_value=computer_network1)
    compute_node2.edit(subordination_value=computer_network1)
    compute_node3.edit(subordination_value=computer_network2)

    self._installSoftware(compute_node1, self.software_instance.getUrlString())
    self._installSoftware(compute_node2, self.software_instance.getUrlString())
    self._installSoftware(compute_node3, self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.assertEqual(None, self.requested_software_instance.getAggregateValue(
        portal_type='Compute Partition'))


    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % compute_node1.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        self.software_instance.getAggregate(portal_type='Compute Partition'),
        partition1.getRelativeUrl(),
    )

    software_instance2 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.instance_tree.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    software_instance2.validate()
    self.commit()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        software_instance2.getAggregate(portal_type='Compute Partition'),
        partition3.getRelativeUrl(),
    )

    software_instance3 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance3.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.instance_tree.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance3, 'start_requested')
    software_instance3.validate()
    self.tic()

    software_instance3.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance3.getAggregate(portal_type='Compute Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_no_network(self):
    """
    Test that when we request instance with mode as 'unique_by_network',
    instance is not deployed on compute_node with no network.
    """
    self._makeTree()
    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>""")
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        self.software_instance.getAggregate(portal_type='Compute Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_check_serialize_called(self):
    """
    Test that on being_requested serialise is being called
    code stolen from testERP5Security:test_MultiplePersonReferenceConcurrentTransaction
    """
    class DummyTestException(Exception):
      pass

    def verify_serialize_call(self):
      # it is checking that anything below compute_node_module raises exception
      # thanks to this this test do not have to be destructive
      if self.getPortalType() == "Instance Tree":
        raise DummyTestException
      else:
        return self.serialize_call()

    self._makeTree()
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>""")

    from Products.ERP5Type.Base import Base
    Base.serialize_call = Base.serialize
    try:
      Base.serialize = verify_serialize_call
      self.assertRaises(DummyTestException,
        self.software_instance.SoftwareInstance_tryToAllocatePartition)
    finally:
      Base.serialize = Base.serialize_call

    transaction.abort()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_no_parallel(self):
    """
    Test that when we request two instances of the same Instance Tree
    with mode as 'unique_by_network' at the same time, they don't get
    allocated to the same network.
    """
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    compute_node1 = self._makeComputeNode()[0]
    compute_node2 = self._makeComputeNode()[0]
    self._installSoftware(compute_node1, self.software_instance.getUrlString())
    self._installSoftware(compute_node2, self.software_instance.getUrlString())

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    compute_node1.edit(subordination_value=computer_network)
    compute_node2.edit(subordination_value=computer_network)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance2 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.instance_tree.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    self.tic()


    self.assertEqual(None,
      self.software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(self.software_instance.getSlapState(), 'start_requested')
    self.assertEqual(self.software_instance.getValidationState(), 'validated')

    self.software_instance.setSlaXml(sla_xml)
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    software_instance2.SoftwareInstance_tryToAllocatePartition()

    portal_workflow = self.software_instance.portal_workflow
    last_workflow_item = portal_workflow.getInfoFor(ob=self.software_instance,
                                          name='comment', wf_id='edit_workflow')
    self.assertEqual(None,last_workflow_item)
    self.assertNotEqual(None,
      self.software_instance.getAggregateValue(portal_type='Compute Partition'))

    # First is deployed
    self.assertEqual(
        computer_network.getReference(),
        self.software_instance.getAggregateValue(portal_type='Compute Partition')\
            .getParentValue().getSubordinationReference(),
    )
    # But second is not yet deployed because of pending activities containing tag
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Compute Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_unexpected_sla_parameter(self):
    self._makeTree()

    self._makeComputeNode()
    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='foo'>bar</parameter>
        </instance>""")
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  def check_allocation_category_sla(self, base_category, compute_node_category,
                                    other_category):
    self._makeTree()

    self._makeComputeNode()
    self.assertEqual(self.compute_node.getAllocationScope(), "open/public")
    self.assertEqual(self.compute_node.getCapacityScope(), "open")
    self.compute_node.edit(**{base_category: compute_node_category})
    self.assertEqual(self.compute_node.getAllocationScope(), "open/public")
    self.assertEqual(self.compute_node.getCapacityScope(), "open")

    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    # Another category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, other_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    # No existing category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>foo</parameter>
        </instance>""" % (base_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    # Compute Node category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, compute_node_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()

    if self.software_instance.getAggregate(portal_type='Compute Partition') is None:
      raise ValueError(self.software_instance)
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_group_sla(self):
    return self.check_allocation_category_sla('group', 'vifib', 'ovh')

  @skip('No category available')
  def test_allocation_cpu_core_sla(self):
    return self.check_allocation_category_sla('cpu_core', 'vifib', 'ovh')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_cpu_frequency_sla(self):
    return self.check_allocation_category_sla('cpu_frequency', '1000', '2000')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_cpu_type_sla(self):
    return self.check_allocation_category_sla('cpu_type', 'x86', 'x86/x86_32')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_local_area_network_type_sla(self):
    return self.check_allocation_category_sla('local_area_network_type',
                                              'ethernet', 'wifi')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_memory_size_sla(self):
    return self.check_allocation_category_sla('memory_size', '128', '256')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_memory_type_sla(self):
    return self.check_allocation_category_sla('memory_type', 'ddr2', 'ddr3')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_region_sla(self):
    return self.check_allocation_category_sla('region', 'africa',
                                              'america')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_storage_capacity_sla(self):
    return self.check_allocation_category_sla('storage_capacity', 'finite',
                                              'infinite')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_storage_interface_sla(self):
    return self.check_allocation_category_sla('storage_interface', 'nas', 'san')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_storage_redundancy_sla(self):
    return self.check_allocation_category_sla('storage_redundancy', 'dht', 'raid')

  def check_allocation_capability(self, capability, *bad_capability_list):
    self._makeTree()

    self._makeComputeNode()
    self.partition.edit(subject=capability)

    self._installSoftware(self.compute_node,
        self.software_instance.getUrlString())

    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Compute Partition'))

    for bad_capability in bad_capability_list:
      self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
          <instance>
          <parameter id='capability'>%s</parameter>
          </instance>""" % bad_capability)
      self.software_instance.SoftwareInstance_tryToAllocatePartition()
      try:
        partition = self.software_instance.getAggregate(
            portal_type='Compute Partition')
        self.assertEqual(None, partition)
      except AssertionError:
        raise AssertionError("Allocated %s on %s with capability %s" % (
            bad_capability, partition, capability))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='capability'>%s</parameter>
        </instance>""" % capability)
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Compute Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_capability(self):
    valid_id = self.generateNewId()
    capability = 'toto_' + valid_id

    self.check_allocation_capability(
        capability,

        'tutu_' + self.generateNewId(),
        't%to_' + valid_id,
        '%_' + valid_id,
        '%',

        't_to_' + valid_id,
        '__' + valid_id,
        '_',

        '.*_' + valid_id,
        '.*',
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_capability_percent(self):
    self.check_allocation_capability('%', '_')

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_capability_ipv6(self):
    self.check_allocation_capability('fe80::1ff:fe23:4567:890a', 'fe80::1')
