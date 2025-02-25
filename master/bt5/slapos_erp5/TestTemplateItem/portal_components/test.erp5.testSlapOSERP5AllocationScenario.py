# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2024  Nexedi SA and Contributors.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from DateTime import DateTime

class TestSlapOSAllocationScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):

  def createComputeNodeForOwner(self, computer_owner, project,
      software_release, software_type):
    self.login(computer_owner.getUserId())

    server_title = 'Public Server for %s' % computer_owner.getReference()
    server_id = self.requestComputeNode(server_title, project.getReference())
    compute_node = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=server_id)
    self.setAccessToMemcached(compute_node)
    self.setServerOpenPublic(compute_node)
    self.assertNotEqual(None, compute_node)
    compute_node.generateCertificate()

    self.supplySoftware(compute_node, software_release)

    # format the compute_nodes
    self.formatComputeNode(compute_node)
    software_product, release_variation, type_variation = self.addSoftwareProduct(
      "instance product", project, software_release, software_type
    )

    self.addAllocationSupply("for compute node", compute_node, software_product,
                             release_variation, type_variation)

    self.tic()
    self.logout()
    self.login()

    self.checkServiceSubscriptionRequest(compute_node)
    return compute_node

  def removeSoftwareReleaseFromComputer(self, computer_owner, 
       compute_node, software_release):
    # and uninstall some software on them
    self.logout()
    self.login(computer_owner.getUserId())
    self.supplySoftware(
      compute_node, software_release,
      state='destroyed')

    self.logout()
    # Uninstall from compute_node
    self.login()
    self.simulateSlapgridSR(compute_node)
    self.tic()

  def bootstrapVirtualMasterTestWithProject(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)
    self.tic()
    self.logout()
    self.login()
    project_owner = self.joinSlapOSAsOwner()

    self.logout()
    self.login(sale_person.getUserId())

    # create a default project
    project_relative_url = self.addProject(person=project_owner, currency=currency)

    self.logout()
    self.login()
    project = self.portal.restrictedTraverse(project_relative_url)
    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % project.getRelativeUrl()
      ]
    )
    self.tic()
    return project, project_owner

  def joinSlapOSAsOwner(self):
    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    owner_person = self.joinSlapOS(self.web_site, owner_reference)
    self.login()
    self.tic()
    return owner_person

class TestSlapOSAllocationScenario(TestSlapOSAllocationScenarioMixin):
  """ Minimal allocation specific test scenarios"""

  def test_software_instance_allocation_scenario(self):
    project, owner_person = self.bootstrapVirtualMasterTestWithProject()    
    self.logout()

    # and install some software on them
    software_release = self.generateNewSoftwareReleaseUrl()
    software_type = 'public type'

    compute_node = self.createComputeNodeForOwner(
      computer_owner=owner_person,
      project=project,
      software_release=software_release,
      software_type=software_type)

    before_timestamp = int(float(DateTime()) * 1e6)
    instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(owner_person.getUserId(),
        owner_person.getReference(), instance_title,
        software_release, software_type,
        compute_node, project.getReference())

    self.login(owner_person.getUserId())

    # let's find instances of user and check connection strings
    software_instance = [q.getSuccessorValue() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title][0]

    parameter_dict = software_instance._asParameterDict()
    timestamp = parameter_dict['timestamp']

    self.assertTrue(timestamp > before_timestamp,
      "timestamp: %s < begin:%s" % (timestamp, before_timestamp))

    # At first we expect that partition is modified later them
    # bang_timestamp
    partition = software_instance.getAggregateValue()
    partition_timestamp = int(float(partition.getModificationDate()) * 1e6)
    self.assertEqual(timestamp, partition_timestamp)

    instance_timestamp = int(software_instance.getBangTimestamp())
    self.assertTrue(partition_timestamp > instance_timestamp,
      "partition: %s < instance:%s" % (partition_timestamp, instance_timestamp))

    software_instance.bang(bang_tree=False, comment="Bang from test.")

    parameter_dict = software_instance._asParameterDict()
    timestamp_after_bang = parameter_dict['timestamp']

    self.assertTrue(timestamp_after_bang > timestamp,
      "after_bang: %s < before_bang:%s" % (timestamp_after_bang, timestamp))

    self.assertEqual(partition_timestamp,
      int(float(partition.getModificationDate()) * 1e6))

    instance_timestamp = int(software_instance.getBangTimestamp())
    self.assertTrue(partition_timestamp < instance_timestamp,
      "partition: %s > instance:%s" % (partition_timestamp, instance_timestamp))

    self.assertEqual(timestamp_after_bang, instance_timestamp)

    # One more time to check
    partition.edit(dummy=1)

    parameter_dict = software_instance._asParameterDict()
    timestamp = parameter_dict['timestamp']

    self.assertNotEqual(timestamp,
      int(software_instance.getBangTimestamp()))

    self.assertEqual(int(float(partition.getModificationDate()) * 1e6), timestamp)
    self.assertTrue(timestamp_after_bang < timestamp,
      "after_bang: %s > after_edit:%s" % (timestamp_after_bang, timestamp))

    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition.getReference()][0]
    self.assertEqual(timestamp,
      partition_parameter_dict['_parameter_dict']['timestamp'])
    self.login(owner_person.getUserId())

    # and the instances
    self.checkInstanceUnallocation(owner_person.getUserId(),
        owner_person.getReference(), instance_title,
        software_release, software_type, compute_node,
        project.getReference())

    self.removeSoftwareReleaseFromComputer(owner_person,
      compute_node, software_release)

    self.checkERP5StateBeforeExit()

  def test_slave_instance_allocation_scenario(self):
    project, owner_person = self.bootstrapVirtualMasterTestWithProject()
    self.logout()

    # and install some software on them
    software_release = self.generateNewSoftwareReleaseUrl()
    software_type = 'public type'

    compute_node = self.createComputeNodeForOwner(
      computer_owner=owner_person,
      project=project,
      software_release=software_release,
      software_type=software_type)

    before_timestamp = int(float(DateTime()) * 1e6)
    instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(owner_person.getUserId(),
        owner_person.getReference(), instance_title,
        software_release, software_type,
        compute_node, project.getReference())

    self.login(owner_person.getUserId())

    # let's find instances of user and check connection strings
    partition_reference = [q.getSuccessorValue().getAggregateReference() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title][0]

    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_timestamp,
      "timestamp: %s < begin:%s" % (timestamp, before_timestamp))

    self.login(owner_person.getUserId())
    instance_node_title = 'Shared Instance for %s' % owner_person.getReference()
    # Convert the Software Instance into an Instance Node
    # to explicitely mark it as accepting Slave Instance
    software_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Software Instance', title=instance_title)
    before_allocation_instance_timestamp = software_instance.getBangTimestamp()

    instance_node = self.addInstanceNode(instance_node_title, software_instance)

    slave_server_software = self.generateNewSoftwareReleaseUrl()
    slave_instance_type = 'slave type'
    software_product, slave_software_release, software_type = self.addSoftwareProduct(
      'share product', project, slave_server_software, slave_instance_type
    )
    self.addAllocationSupply("for instance node", instance_node,
     software_product, slave_software_release, software_type)

    slave_instance_title = 'Slave title %s' % self.generateNewId()
    self.checkSlaveInstanceAllocation(owner_person.getUserId(),
        owner_person.getReference(), slave_instance_title,
        slave_server_software, slave_instance_type,
        compute_node, project.getReference())

    self.login(owner_person.getUserId())
    before_allocation_timestamp = timestamp
    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_allocation_timestamp,
      "timestamp: %s < before_allocation_timestamp:%s" % (timestamp, before_allocation_timestamp))

    self.assertTrue(timestamp > before_allocation_instance_timestamp,
      "timestamp: %s < before_instance_allocation:%s" % (timestamp, before_allocation_instance_timestamp))

    slave_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Slave Instance', title=slave_instance_title)

    # The slave instance was bang so that's why timestamp was updated,
    # this ensure response to server is updated.
    self.assertEqual(timestamp,
      int(slave_instance.getBangTimestamp()))
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 1)
    self.assertEqual(parameter_slave_list[0]['timestamp'], timestamp)

    self.login(owner_person.getUserId())
    self.checkSlaveInstanceUnallocation(
      owner_person.getUserId(),
      owner_person.getReference(), slave_instance_title,
      slave_server_software, slave_instance_type, compute_node,
      project.getReference())

    self.tic()

    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 0)
    timestamp_before_unallocation = timestamp
    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']

    self.assertNotEqual(timestamp_before_unallocation, timestamp)
    self.assertTrue(timestamp > timestamp_before_unallocation,
      "timestamp: %s < before_unallocation:%s" % (timestamp, timestamp_before_unallocation))

    self.removeSoftwareReleaseFromComputer(owner_person,
      compute_node, software_release)

    self.checkERP5StateBeforeExit()

  def test_stopped_slave_instance_allocation_scenario(self):
    project, owner_person = self.bootstrapVirtualMasterTestWithProject()    
    self.logout()

    # and install some software on them
    software_release = self.generateNewSoftwareReleaseUrl()
    software_type = 'public type'

    compute_node = self.createComputeNodeForOwner(
      computer_owner=owner_person,
      project=project,
      software_release=software_release,
      software_type=software_type)

    before_timestamp = int(float(DateTime()) * 1e6)
    instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(owner_person.getUserId(),
        owner_person.getReference(), instance_title,
        software_release, software_type,
        compute_node, project.getReference())

    self.login(owner_person.getUserId())

    # let's find instances of user and check connection strings
    partition_reference = [q.getSuccessorValue().getAggregateReference() for q in
        self._getCurrentInstanceTreeList()
        if q.getTitle() == instance_title][0]

    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_timestamp,
      "timestamp: %s < begin:%s" % (timestamp, before_timestamp))

    self.login(owner_person.getUserId())
    instance_node_title = 'Shared Instance for %s' % owner_person.getReference()
    # Convert the Software Instance into an Instance Node
    # to explicitely mark it as accepting Slave Instance
    software_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Software Instance', title=instance_title)
    before_allocation_instance_timestamp = software_instance.getBangTimestamp()

    instance_node = self.addInstanceNode(instance_node_title, software_instance)

    slave_server_software = self.generateNewSoftwareReleaseUrl()
    slave_instance_type = 'slave type'
    software_product, slave_software_release, software_type = self.addSoftwareProduct(
      'share product', project, slave_server_software, slave_instance_type
    )
    self.addAllocationSupply("for instance node", instance_node,
     software_product, slave_software_release, software_type)

    slave_instance_title = 'Slave title %s' % self.generateNewId()
    self.checkSlaveInstanceAllocation(owner_person.getUserId(),
        owner_person.getReference(), slave_instance_title,
        slave_server_software, slave_instance_type,
        compute_node, project.getReference())

    self.login(owner_person.getUserId())
    before_allocation_timestamp = timestamp
    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_allocation_timestamp,
      "timestamp: %s < before_allocation_timestamp:%s" % (timestamp, before_allocation_timestamp))

    self.assertTrue(timestamp > before_allocation_instance_timestamp,
      "timestamp: %s < before_instance_allocation:%s" % (timestamp, before_allocation_instance_timestamp))

    slave_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Slave Instance', title=slave_instance_title)

    # The slave instance was bang so that's why timestamp was updated,
    # this ensure response to server is updated.
    self.assertEqual(timestamp,
      int(slave_instance.getBangTimestamp()))
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 1)
    self.assertEqual(parameter_slave_list[0]['timestamp'], timestamp)

    self.login(owner_person.getUserId())
    self.personRequestInstance(
      software_release=slave_server_software,
      software_type=slave_instance_type,
      partition_reference=slave_instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      state='<marshal><string>stopped</string></marshal>',
      project_reference=project.getReference()
    )

    self.simulateSlapgridCP(compute_node)
    self.tic()

    self.assertEqual(slave_instance.getSlapState(), 'stop_requested')
    before_stop_timestamp = timestamp
    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_stop_timestamp,
      "timestamp: %s < before_stop_timestamp:%s" % (timestamp, before_stop_timestamp))

    self.assertEqual(timestamp,
      int(software_instance.getBangTimestamp()))
    # no entry expected
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 0)

    # Start again and re-check if the timestamp was updated
    self.login(owner_person.getUserId())
    self.personRequestInstance(
      software_release=slave_server_software,
      software_type=slave_instance_type,
      partition_reference=slave_instance_title,
      shared_xml='<marshal><bool>1</bool></marshal>',
      state='<marshal><string>started</string></marshal>',
      project_reference=project.getReference()
    )

    self.simulateSlapgridCP(compute_node)
    self.tic()

    before_start_timestamp = timestamp
    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]

    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']
    self.assertTrue(timestamp > before_start_timestamp,
      "timestamp: %s < before_start_timestamp:%s" % (timestamp, before_start_timestamp))

    # The slave instance was bang so that's why timestamp was updated,
    # this ensure response to server is updated.
    self.assertEqual(timestamp,
      int(slave_instance.getBangTimestamp()))
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 1)
    self.assertEqual(parameter_slave_list[0]['timestamp'], timestamp)

    self.login(owner_person.getUserId())
    self.checkSlaveInstanceUnallocation(
      owner_person.getUserId(),
      owner_person.getReference(), slave_instance_title,
      slave_server_software, slave_instance_type, compute_node,
      project.getReference())

    self.tic()

    computer_information_dict = compute_node._getCacheComputeNodeInformation(None)
    # Ensure compute node gets the proper timestamp
    partition_parameter_dict = [d 
      for d in computer_information_dict['_computer_partition_list'] 
        if d['partition_id'] == partition_reference][0]
    parameter_slave_list = partition_parameter_dict['_parameter_dict']['slave_instance_list']
    self.assertEqual(len(parameter_slave_list), 0)
    timestamp_before_unallocation = timestamp
    timestamp = partition_parameter_dict['_parameter_dict']['timestamp']

    self.assertNotEqual(timestamp_before_unallocation, timestamp)
    self.assertTrue(timestamp > timestamp_before_unallocation,
      "timestamp: %s < before_unallocation:%s" % (timestamp, timestamp_before_unallocation))

    self.removeSoftwareReleaseFromComputer(owner_person,
      compute_node, software_release)

    self.checkERP5StateBeforeExit()
