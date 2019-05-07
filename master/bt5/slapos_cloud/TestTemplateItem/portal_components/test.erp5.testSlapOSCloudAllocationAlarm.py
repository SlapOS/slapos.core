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

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self._simulatePerson_isNotAllowedToAllocate()
    try:
      self.software_instance.SoftwareInstance_tryToAllocatePartition()
    finally:
      self._dropPerson_isAllowedToAllocate()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.assertEqual(
        'Allocation failed: Allocation disallowed',
        self.software_instance.workflow_history['edit_workflow'][-1]['comment'])

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_no_free_partition(self):
    self._makeTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_no_host_instance(self):
    self._makeSlaveTree()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

  def _installSoftware(self, computer, url):
    software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    software_installation.edit(url_string=url,
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        aggregate=computer.getRelativeUrl())
    software_installation.validate()
    software_installation.requestStart()
    self.tic()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_free_partition(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def _allocateHost(self, software_instance, computer_partition):
    software_instance.edit(
        aggregate_value=computer_partition
        )
    computer_partition.markBusy()
    self.tic()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_instance(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_capacity_scope_close(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_capacity_scope_close(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_allocation_scope_close(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_allocation_scope_close(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_allocation_scope_open_personal(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    self.computer.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_allocation_scope_open_personal(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    self.computer.edit(allocation_scope='open/personal',
      source_administration=self.person_user.getRelativeUrl())
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_allocation_scope_open_friend(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())
    # change computer owner
    new_id = self.generateNewId()
    person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    for assignment in person_user.contentValues(portal_type="Assignment"):
      assignment.open()

    self.computer.edit(
      source_administration=person_user.getRelativeUrl(),
      destination_section=self.person_user.getRelativeUrl(),
      allocation_scope='open/friend')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_host_allocation_scope_open_friend(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)
    # change computer owner
    new_id = self.generateNewId()
    person_user = self.portal.person_module.template_member.\
                                 Base_createCloneDocument(batch_mode=1)
    person_user.edit(
      title="live_test_%s" % new_id,
      reference="live_test_%s" % new_id,
      default_email_text="live_test_%s@example.org" % new_id,
    )

    person_user.validate()
    for assignment in person_user.contentValues(portal_type="Assignment"):
      assignment.open()

    self.computer.edit(
      source_administration=person_user.getRelativeUrl(),
      destination_section=self.person_user.getRelativeUrl(),
      allocation_scope='open/friend')
    self.tic()

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_does_not_fail_on_instance_with_damaged_sla_xml(self):
    self._makeTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    transaction.abort()

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_does_not_fail_on_slave_with_damaged_sla_xml(self):
    self._makeSlaveTree()

    self.software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))
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

    self._makeComputer()
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

    self._makeComputer()
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

    self._makeComputer()
    self.assertEqual(self.computer.getAllocationScope(), "open/public")
    self.assertEqual(self.computer.getCapacityScope(), "open")

    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s_foo' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s' % self.partition.getParentValue().getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_instance_guid(self):
    self._makeSlaveTree()

    self._makeComputer()
    self._allocateHost(self.requested_software_instance,
        self.partition)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s' % \
        self.requested_software_instance.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_network_guid(self):
    self._makeTree()

    self._makeComputer()
    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    self.computer.edit(
        subordination_value=computer_network)
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s' % \
          self.partition.getParentValue().getSubordinationReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_one_network(self):
    """
    Test that when mode is "unique_by_network", we deploy new instance on
    computer network not already used by any software instance of the
    hosting subscription.
    Then test that we do NOT deploy new instance on
    computer network already used by any software instance of the
    hosting subscription.
    """
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    computer1 = self._makeComputer()[0]
    computer2 = self._makeComputer()[0]
    self._installSoftware(computer1, self.software_instance.getUrlString())
    self._installSoftware(computer2, self.software_instance.getUrlString())

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    computer1.edit(subordination_value=computer_network)
    computer2.edit(subordination_value=computer_network)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    software_instance2 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.hosting_subscription.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    self.tic()

    self.assertEqual(None,
      self.software_instance.getAggregateValue(portal_type='Computer Partition'))

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
      self.software_instance.getAggregateValue(portal_type='Computer Partition'))

    self.assertEqual(
        computer_network.getReference(),
        self.software_instance.getAggregateValue(portal_type='Computer Partition')\
            .getParentValue().getSubordinationReference(),
    )

    self.tic()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Computer Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_several_network(self):
    """
    Test that when mode is "unique_by_network", we deploy new instance on
    computer network not already used by any software instance of the
    hosting subscription.
    Then test that we do NOT deploy new instance on
    computer network already used by any software instance of the
    hosting subscription.
    Test with 3 instances and 3 existing computers on 2 different networks.
    """
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    computer1, partition1 = self._makeComputer()
    computer2 = self._makeComputer()[0]
    computer3, partition3 = self._makeComputer()
    computer_network1 = self._makeComputerNetwork()
    computer_network2 = self._makeComputerNetwork()

    computer1.edit(subordination_value=computer_network1)
    computer2.edit(subordination_value=computer_network1)
    computer3.edit(subordination_value=computer_network2)

    self._installSoftware(computer1, self.software_instance.getUrlString())
    self._installSoftware(computer2, self.software_instance.getUrlString())
    self._installSoftware(computer3, self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % computer1.getReference())
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        self.software_instance.getAggregate(portal_type='Computer Partition'),
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
      specialise=self.hosting_subscription.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    software_instance2.validate()
    self.tic()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        software_instance2.getAggregate(portal_type='Computer Partition'),
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
      specialise=self.hosting_subscription.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance3, 'start_requested')
    software_instance3.validate()
    self.tic()

    software_instance3.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance3.getAggregate(portal_type='Computer Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_mode_unique_by_network_no_network(self):
    """
    Test that when we request instance with mode as 'unique_by_network',
    instance is not deployed on computer with no network.
    """
    self._makeTree()
    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>""")
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        self.software_instance.getAggregate(portal_type='Computer Partition')
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
      # it is checking that anything below computer_module raises exception
      # thanks to this this test do not have to be destructive
      if self.getPortalType() == "Hosting Subscription":
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
    Test that when we request two instances of the same Hosting Subscription
    with mode as 'unique_by_network' at the same time, they don't get
    allocated to the same network.
    """
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    self._makeTree()
    computer1 = self._makeComputer()[0]
    computer2 = self._makeComputer()[0]
    self._installSoftware(computer1, self.software_instance.getUrlString())
    self._installSoftware(computer2, self.software_instance.getUrlString())

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    computer1.edit(subordination_value=computer_network)
    computer2.edit(subordination_value=computer_network)

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    software_instance2 = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=self.software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=self.hosting_subscription.getRelativeUrl(),
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    self.tic()


    self.assertEqual(None,
      self.software_instance.getAggregateValue(portal_type='Computer Partition'))

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
      self.software_instance.getAggregateValue(portal_type='Computer Partition'))

    # First is deployed
    self.assertEqual(
        computer_network.getReference(),
        self.software_instance.getAggregateValue(portal_type='Computer Partition')\
            .getParentValue().getSubordinationReference(),
    )
    # But second is not yet deployed because of pending activities containing tag
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Computer Partition')
    )

  @simulate('Person_isAllowedToAllocate', '*args, **kwargs', 'return True')
  def test_allocation_unexpected_sla_parameter(self):
    self._makeTree()

    self._makeComputer()
    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='foo'>bar</parameter>
        </instance>""")
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

  def check_allocation_category_sla(self, base_category, computer_category,
                                    other_category):
    self._makeTree()

    self._makeComputer()
    self.assertEqual(self.computer.getAllocationScope(), "open/public")
    self.assertEqual(self.computer.getCapacityScope(), "open")
    self.computer.edit(**{base_category: computer_category})
    self.assertEqual(self.computer.getAllocationScope(), "open/public")
    self.assertEqual(self.computer.getCapacityScope(), "open")

    self._installSoftware(self.computer,
        self.software_instance.getUrlString())

    self.assertEqual(None, self.software_instance.getAggregateValue(
        portal_type='Computer Partition'))

    # Another category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, other_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    # No existing category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>foo</parameter>
        </instance>""" % (base_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        self.software_instance.getAggregate(portal_type='Computer Partition'))

    # Computer category
    self.software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, computer_category))
    self.software_instance.SoftwareInstance_tryToAllocatePartition()

    if self.software_instance.getAggregate(portal_type='Computer Partition') is None:
      raise ValueError(self.software_instance)
    self.assertEqual(self.partition.getRelativeUrl(),
        self.software_instance.getAggregate(portal_type='Computer Partition'))

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
