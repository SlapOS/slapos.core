# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
import transaction
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, TemporaryAlarmScript
from unittest import skip


class TestSlapOSAllocation(SlapOSTestCaseMixin):

  launch_caucase = 1

  def makeAllocableComputeNode(self, project, software_product,
                               release_variation, type_variation):
    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      compute_node, partition = self._makeComputeNode(project)
      self.addAllocationSupply("for compute node", compute_node, software_product,
                               release_variation, type_variation)
      self._installSoftware(
        compute_node,
        release_variation.getUrlString()
      )
      open_order = self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
      )
      open_order.newContent(
        aggregate_value=compute_node
      )
      self.portal.portal_workflow._jumpToStateFor(open_order, 'validated')
      self.tic()
    return compute_node, partition

  def makeAllocableSoftwareInstanceAndProduct(self, allocation_state='possible',
                                              shared=False, node="compute"):
    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      software_product, release_variation, type_variation, compute_node, partition, instance_tree = \
        self.bootstrapAllocableInstanceTree(allocation_state=allocation_state, shared=shared, node=node)

      self.addAllocationSupply("for compute node", compute_node, software_product,
                               release_variation, type_variation)
      real_compute_node = partition.getParentValue()
      self._installSoftware(
        real_compute_node,
        release_variation.getUrlString()
      )
      self.tic()

    self.assertEqual(real_compute_node.getAllocationScope(), "open")
    self.assertEqual(real_compute_node.getCapacityScope(), "open")

    software_instance = instance_tree.getSuccessorValue()

    return software_instance, compute_node, partition, software_product, release_variation, type_variation

  def makeAllocableSoftwareInstance(self, allocation_state='possible', shared=False, node="compute"):
    software_instance, compute_node, partition, _, _, _ = \
      self.makeAllocableSoftwareInstanceAndProduct(allocation_state=allocation_state, shared=shared, node=node)
    return software_instance, compute_node, partition

  def _installSoftware(self, compute_node, url):
    software_installation = self.portal.software_installation_module\
        .newContent(portal_type="Software Installation")
    software_installation.edit(url_string=url,
        reference='TESTSOFTINST-%s' % self.generateNewId(),
        aggregate=compute_node.getRelativeUrl())
    software_installation.validate()
    software_installation.requestStart()
    self.tic()
    compute_node.reindexObject()
    self.tic()

  def test_allocation_no_free_partition(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance()
    partition.markBusy()
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

  def test_allocation_no_host_instance(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance(shared=True, node="instance")
    partition.markFree()
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

  def test_allocation_free_partition(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

  def _allocateHost(self, software_instance, compute_partition):
    software_instance.edit(
        aggregate_value=compute_partition
        )
    compute_partition.markBusy()
    self.tic()

  def test_allocation_host_instance(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance(shared=True, node="instance")

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_capacity_scope_close(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance()
    partition.getParentValue().edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_host_capacity_scope_close(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance(shared=True, node="instance")
    partition.getParentValue().edit(capacity_scope='close')
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_allocation_scope_close(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance()
    partition.getParentValue().edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_host_allocation_scope_close(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance(shared=True, node="instance")
    partition.getParentValue().edit(allocation_scope='close')
    self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_does_not_fail_on_instance_with_damaged_sla_xml(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance()

    software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    transaction.abort()

  def test_allocation_does_not_fail_on_slave_with_damaged_sla_xml(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance(shared=True, node="instance")

    software_instance.setSlaXml('this is not xml')
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))
    transaction.abort()

  ##################################################
  # alarm slapos_allocate_instance
  ##################################################
  def test_alarm_software_instance_unallocated(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance()

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()

    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_slave_instance_unallocated(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance(shared=True, node="instance")

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()

    self.assertEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_software_instance_allocated(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance(allocation_state='allocated')

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()

    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        software_instance.workflow_history['edit_workflow'][-1]['comment'])

  def test_alarm_slave_instance_allocated(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance(allocation_state='allocated', shared=True, node="instance")

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.portal.portal_alarms.slapos_allocate_instance.activeSense()
      self.tic()

    self.assertNotEqual(
        'Visited by SoftwareInstance_tryToAllocatePartition',
        software_instance.workflow_history['edit_workflow'][-1]['comment'])

  ##################################################
  # SoftwareInstance_tryToAllocatePartition
  ##################################################
  def test_allocation_computer_guid(self):
    software_instance, compute_node, partition = self.makeAllocableSoftwareInstance()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s_foo' % compute_node.getReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % '%s' % compute_node.getReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_instance_guid(self):
    software_instance, _, partition = self.makeAllocableSoftwareInstance(shared=True, node="instance")
    requested_software_instance = partition.getAggregateRelatedValue()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
        requested_software_instance.getReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='instance_guid'>%s</parameter>
        </instance>""" % '%s' % \
        requested_software_instance.getReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_network_guid(self):
    software_instance, compute_node, partition = self.makeAllocableSoftwareInstance()

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id,
        follow_up_value=software_instance.getFollowUpValue()
    )
    computer_network.validate()
    compute_node.edit(
      subordination_value=computer_network
    )
    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s_foo' % \
          partition.getParentValue().getSubordinationReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='network_guid'>%s</parameter>
        </instance>""" % '%s' % \
          partition.getParentValue().getSubordinationReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

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
    software_instance, compute_node1, _, software_product, release_variation, type_variation = \
      self.makeAllocableSoftwareInstanceAndProduct()

    instance_tree = software_instance.getSpecialiseValue()
    project = compute_node1.getFollowUpValue()

    compute_node2, _ = self.makeAllocableComputeNode(project, software_product, release_variation, type_variation)

    new_id = self.generateNewId()
    computer_network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        title="live_test_%s" % new_id,
        reference="live_test_%s" % new_id)
    computer_network.validate()
    compute_node1.edit(subordination_value=computer_network)
    compute_node2.edit(subordination_value=computer_network)

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance2 = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=software_instance.getUrlString(),
      source_reference=software_instance.getSourceReference(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise_value=instance_tree,
      follow_up_value=project,
      ssl_key='foo',
      ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None,
      software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(software_instance.getSlapState(), 'start_requested')
    self.assertEqual(software_instance.getValidationState(), 'validated')

    software_instance.setSlaXml(sla_xml)
    software_instance.SoftwareInstance_tryToAllocatePartition()

    self.tic()
    portal_workflow = software_instance.portal_workflow
    last_workflow_item = portal_workflow.getInfoFor(ob=software_instance,
                                          name='comment', wf_id='edit_workflow')
    self.assertEqual(None, last_workflow_item)
    self.assertNotEqual(None,
      software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(
        computer_network.getReference(),
        software_instance.getAggregateValue(portal_type='Compute Partition')\
                         .getParentValue().getSubordinationReference(),
    )

    self.tic()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Compute Partition')
    )

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
    sla_xml = """<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>"""
    software_instance, compute_node1, partition1, software_product, release_variation, type_variation = \
      self.makeAllocableSoftwareInstanceAndProduct()

    instance_tree = software_instance.getSpecialiseValue()
    project = compute_node1.getFollowUpValue()

    compute_node2, _ = self.makeAllocableComputeNode(project, software_product, release_variation, type_variation)
    compute_node3, partition3 = self.makeAllocableComputeNode(project, software_product, release_variation, type_variation)

    computer_network1 = self._makeComputerNetwork()
    computer_network2 = self._makeComputerNetwork()

    compute_node1.edit(subordination_value=computer_network1)
    compute_node2.edit(subordination_value=computer_network1)
    compute_node3.edit(subordination_value=computer_network2)

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        <parameter id='computer_guid'>%s</parameter>
        </instance>""" % compute_node1.getReference())
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        software_instance.getAggregate(portal_type='Compute Partition'),
        partition1.getRelativeUrl(),
    )

    software_instance2 = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=software_instance.getUrlString(),
      source_reference=software_instance.getSourceReference(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=instance_tree.getRelativeUrl(),
      follow_up_value=project,
      ssl_key='foo',
      ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    software_instance2.validate()
    self.tic()
    software_instance2.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        software_instance2.getAggregate(portal_type='Compute Partition'),
        partition3.getRelativeUrl(),
    )

    software_instance3 = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    software_instance3.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=software_instance.getUrlString(),
      source_reference=self.generateNewSoftwareType(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise=instance_tree.getRelativeUrl(),
      follow_up_value=project,
      ssl_key='foo',
      ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance3, 'start_requested')
    software_instance3.validate()
    self.tic()

    software_instance3.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance3.getAggregate(portal_type='Compute Partition')
    )

  def test_allocation_mode_unique_by_network_no_network(self):
    """
    Test that when we request instance with mode as 'unique_by_network',
    instance is not deployed on compute_node with no network.
    """
    software_instance, _, _ = self.makeAllocableSoftwareInstance()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>""")
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(
        None,
        software_instance.getAggregate(portal_type='Compute Partition')
    )

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

    software_instance, _, _ = self.makeAllocableSoftwareInstance()
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='mode'>unique_by_network</parameter>
        </instance>""")

    from Products.ERP5Type.Base import Base
    Base.serialize_call = Base.serialize
    try:
      Base.serialize = verify_serialize_call
      self.assertRaises(DummyTestException,
        software_instance.SoftwareInstance_tryToAllocatePartition)
    finally:
      Base.serialize = Base.serialize_call

    transaction.abort()

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
    software_instance, compute_node1, _, software_product, release_variation, type_variation = \
      self.makeAllocableSoftwareInstanceAndProduct()

    instance_tree = software_instance.getSpecialiseValue()
    project = compute_node1.getFollowUpValue()

    compute_node2, _ = self.makeAllocableComputeNode(project, software_product, release_variation, type_variation)

    computer_network = self._makeComputerNetwork()

    compute_node1.edit(subordination_value=computer_network)
    compute_node2.edit(subordination_value=computer_network)

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance2 = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")
    software_instance2.edit(
      title=self.generateNewSoftwareTitle(),
      reference="TESTSI-%s" % self.generateNewId(),
      url_string=software_instance.getUrlString(),
      source_reference=software_instance.getSourceReference(),
      text_content=self.generateSafeXml(),
      sla_xml=sla_xml,
      specialise_value=instance_tree,
      follow_up_value=project,
      ssl_key='foo',
      ssl_certificate='bar'
    )
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'start_requested')
    self.portal.portal_workflow._jumpToStateFor(software_instance2, 'validated')
    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None,
      software_instance.getAggregateValue(portal_type='Compute Partition'))

    self.assertEqual(software_instance.getSlapState(), 'start_requested')
    self.assertEqual(software_instance.getValidationState(), 'validated')

    software_instance.setSlaXml(sla_xml)
    software_instance.SoftwareInstance_tryToAllocatePartition()
    software_instance2.SoftwareInstance_tryToAllocatePartition()

    portal_workflow = software_instance.portal_workflow
    last_workflow_item = portal_workflow.getInfoFor(ob=software_instance,
                                          name='comment', wf_id='edit_workflow')
    self.assertEqual(None, last_workflow_item)
    self.assertNotEqual(None,
      software_instance.getAggregateValue(portal_type='Compute Partition'))

    # First is deployed
    self.assertEqual(
        computer_network.getReference(),
        software_instance.getAggregateValue(portal_type='Compute Partition')\
                         .getParentValue().getSubordinationReference(),
    )
    # But second is not yet deployed because of pending activities containing tag
    self.assertEqual(
        None,
        software_instance2.getAggregate(portal_type='Compute Partition')
    )

  def test_allocation_unexpected_sla_parameter(self):
    software_instance, _, _ = self.makeAllocableSoftwareInstance()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='foo'>bar</parameter>
        </instance>""")
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

  def check_allocation_category_sla(self, base_category, compute_node_category,
                                    other_category):
    software_instance, compute_node, partition = self.makeAllocableSoftwareInstance()

    compute_node.edit(**{base_category: compute_node_category})
    self.assertEqual(compute_node.getAllocationScope(), "open")
    self.assertEqual(compute_node.getCapacityScope(), "open")

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    # Another category
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, other_category))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

    # No existing category
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>foo</parameter>
        </instance>""" % (base_category))
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(None,
        software_instance.getAggregate(portal_type='Compute Partition'))

    # Compute Node category
    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='%s'>%s</parameter>
        </instance>""" % (base_category, compute_node_category))
    software_instance.SoftwareInstance_tryToAllocatePartition()

    self.assertEqual(
      partition.getRelativeUrl(),
      software_instance.getAggregate(portal_type='Compute Partition'),
      software_instance.getRelativeUrl()
    )

  def test_allocation_group_sla(self):
    return self.check_allocation_category_sla('group', 'vifib', 'ovh')

  @skip('No category available')
  def test_allocation_cpu_core_sla(self):
    return self.check_allocation_category_sla('cpu_core', 'vifib', 'ovh')

  def test_allocation_cpu_frequency_sla(self):
    return self.check_allocation_category_sla('cpu_frequency', '1000', '2000')

  def test_allocation_cpu_type_sla(self):
    return self.check_allocation_category_sla('cpu_type', 'x86', 'x86/x86_32')

  def test_allocation_local_area_network_type_sla(self):
    return self.check_allocation_category_sla('local_area_network_type',
                                              'ethernet', 'wifi')

  def test_allocation_memory_size_sla(self):
    return self.check_allocation_category_sla('memory_size', '128', '256')

  def test_allocation_memory_type_sla(self):
    return self.check_allocation_category_sla('memory_type', 'ddr2', 'ddr3')

  def test_allocation_region_sla(self):
    return self.check_allocation_category_sla('region', 'africa',
                                              'america')

  def test_allocation_storage_capacity_sla(self):
    return self.check_allocation_category_sla('storage_capacity', 'finite',
                                              'infinite')

  def test_allocation_storage_interface_sla(self):
    return self.check_allocation_category_sla('storage_interface', 'nas', 'san')

  def test_allocation_storage_redundancy_sla(self):
    return self.check_allocation_category_sla('storage_redundancy', 'dht', 'raid')

  def check_allocation_capability(self, capability, bad_capability_list,
                                  good_capability=None):
    good_capability = good_capability or capability

    software_instance, compute_node, partition = self.makeAllocableSoftwareInstance()

    partition.edit(subject=capability)
    self.assertEqual(compute_node.getAllocationScope(), "open")
    self.assertEqual(compute_node.getCapacityScope(), "open")

    with TemporaryAlarmScript(self.portal, 'SoftwareInstance_tryToAllocatePartition'):
      self.tic()

    self.assertEqual(None, software_instance.getAggregateValue(
        portal_type='Compute Partition'))

    for bad_capability in bad_capability_list:
      software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
          <instance>
          <parameter id='capability'>%s</parameter>
          </instance>""" % bad_capability)
      software_instance.SoftwareInstance_tryToAllocatePartition()
      try:
        allocated_partition = software_instance.getAggregate(
            portal_type='Compute Partition')
        self.assertEqual(None, allocated_partition)
      except AssertionError:
        raise AssertionError("Allocated %s on %s with capability %s" % (
            bad_capability, allocated_partition, capability))

    software_instance.setSlaXml("""<?xml version='1.0' encoding='utf-8'?>
        <instance>
        <parameter id='capability'>%s</parameter>
        </instance>""" % good_capability)
    software_instance.SoftwareInstance_tryToAllocatePartition()
    self.assertEqual(partition.getRelativeUrl(),
        software_instance.getAggregate(portal_type='Compute Partition'))

  def test_allocation_capability(self):
    valid_id = self.generateNewId()
    capability = 'toto_' + valid_id

    self.check_allocation_capability(capability, (
        'tutu_' + self.generateNewId(),
        't%to_' + valid_id,
        '%_' + valid_id,
        '%',

        't_to_' + valid_id,
        '__' + valid_id,
        '_',

        '.*_' + valid_id,
        '.*',
    ))

  def test_allocation_capability_percent(self):
    self.check_allocation_capability('%', ('_',))

  def test_allocation_capability_ipv6(self):
    self.check_allocation_capability('fe80::1ff:fe23:4567:890a', ('fe80::1',))

  def test_allocation_capability_multiple(self):
    self.check_allocation_capability('toto\ntata', ('titi',), 'toto')
    self.check_allocation_capability('toto\ntata', ('titi',), 'tata')
