# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSRemoteNodeChangeRequestScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):
  pass


class TestSlapOSRemoteNodeChangeRequestScenario(TestSlapOSRemoteNodeChangeRequestScenarioMixin):

  def test_empty_remote_node_transfer_to_workrgrop_scenario(self):
    self.test_empty_remote_node_transfer_scenario(scenario='workgroup')

  def test_empty_remote_node_transfer_from_workgroup_scenario(self):
    self.test_empty_remote_node_transfer_scenario(scenario='remote_workgroup')

  def test_empty_remote_node_transfer_scenario(self, scenario='default'):
    with PinnedDateTime(self, DateTime('2024/02/17')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

      # lets join as slapos administrator, which will own few compute_nodes
      remote_owner_reference = 'remote-owner-%s' % self.generateNewId()
      remote_owner_person = self.joinSlapOS(remote_owner_reference)

      self.login(sale_person.getUserId())
      # create a default project
      remote_project = self.addDefaultProject(
        person=remote_owner_person, currency=currency)


      # join as the another visitor and request software instance on public
      # compute_node
      remote_public_reference = 'remote-public-%s' % self.generateNewId()
      remote_public_person = self.joinSlapOS(remote_public_reference)


      ####################################
      # Create a local project
      ####################################
      self.login(sale_person.getUserId())
      # create a default project
      project = self.addDefaultProject(
        person=remote_public_person, currency=currency)

      owner_person = remote_public_person
      remote_entity = remote_public_person
      if scenario == 'remote_workgroup':
        self.login(sale_person.getUserId())
        workgroup = self.createWorkgroup(remote_public_person,
                                         project=remote_project,
                                         currency=currency)
        remote_entity = workgroup

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())

      remote_compute_node = self.requestRemoteNode(
        project, remote_project, remote_entity)

      self.tic()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(public_reference)
      workgroup = None
      destination_section = public_person
      if scenario == 'workgroup':
        self.login(sale_person.getUserId())
        workgroup = self.createWorkgroup(public_person, project=project,
                                         currency=currency)
        destination_section = workgroup

    self.tic()
    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      self.login(sale_person.getUserId())
      # Try now transfer to public person from the workgroup
      remote_node_change_request = destination_section.Person_claimSlaposRemoteNode(
        remote_compute_node.getReference(), None)

      self.tic()
      self.login()
      self.assertEqual(remote_compute_node.getDestinationSection(),
                       destination_section.getRelativeUrl())
      self.assertNotEqual(None, remote_node_change_request)
      self.assertEqual("Remote Node Change Request",
                          remote_node_change_request.getPortalType())
      self.assertEqual("invalidated",
                          remote_node_change_request.getSimulationState())

    # Ensure no unexpected object has been created
    # 3 assignment request
    # 1 remote node
    # 1 credential request
    # 1 open sale order
    # 3 assignment
    # 1 remote node change request
    # 1 sale trade condition
    # 1 subscription request
    expected_amount = 12
    if scenario == 'remote_workgroup':
      # +1 assignment request
      # +1 sale trade condition
      # +1 workgroup
      expected_amount += 3
    self.assertRelatedObjectCount(remote_project, expected_amount)

    # Ensure no unexpected object has been created
    # 3 assignment request
    # 1 remote node
    # 1 credential request
    # 1 open sale order
    # 3 assignment
    # 1 remote node change request
    # 1 sale trade condition
    # 1 subscription request
    expected_amount = 12
    if scenario == 'workgroup':
      # +1 assignment request
      # +1 sale trade condition
      # +1 workgroup
      expected_amount += 3
    self.assertRelatedObjectCount(project, expected_amount)

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.checkERP5StateBeforeExit()

  def test_remote_node_transfer_to_workrgrop_scenario(self):
    self.test_remote_node_transfer_scenario(scenario='workgroup')

  def test_remote_node_transfer_from_workgroup_scenario(self):
    self.test_remote_node_transfer_scenario(scenario='remote_workgroup')

  def test_remote_node_transfer_scenario(self, scenario='default'):
    with PinnedDateTime(self, DateTime('2024/02/17')):
      currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

      # lets join as slapos administrator, which will own few compute_nodes
      remote_owner_reference = 'remote-owner-%s' % self.generateNewId()
      remote_owner_person = self.joinSlapOS(remote_owner_reference)

      self.login(sale_person.getUserId())
      # create a default project
      remote_project = self.addDefaultProject(
        person=remote_owner_person, currency=currency)

      # hooray, now it is time to create compute_nodes
      self.login(remote_owner_person.getUserId())

      remote_server = self.requestComputeNode(
        'Remote Server for %s' % remote_owner_person,
        remote_project.getReference())

      # and install some software on them
      remote_server_software = self.generateNewSoftwareReleaseUrl()
      remote_instance_type = 'public type'

      self.supplySoftware(remote_server, remote_server_software)

      # format the compute_nodes
      self.formatComputeNode(remote_server)

      remote_software_product, remote_release_variation, remote_type_variation = self.addSoftwareProduct(
        "remote product", remote_project, remote_server_software, remote_instance_type
      )

      self.addAllocationSupply("for compute node", remote_server, remote_software_product,
                               remote_release_variation, remote_type_variation)

      # join as the another visitor and request software instance on public
      # compute_node
      remote_public_reference = 'remote-public-%s' % self.generateNewId()
      remote_public_person = self.joinSlapOS(remote_public_reference)


      ####################################
      # Create a local project
      ####################################
      self.login(sale_person.getUserId())
      # create a default project
      project = self.addDefaultProject(
        person=remote_public_person, currency=currency)

      owner_person = remote_public_person
      public_reference2 = 'public2-%s' % self.generateNewId()
      public_person2 = self.joinSlapOS(public_reference2)
      remote_entity = public_person2
      if scenario == "remote_workgroup":
        self.login(sale_person.getUserId())
        remote_workgroup = self.createWorkgroup(public_person2,
                                         project=remote_project,
                                         currency=currency)
        remote_entity = remote_workgroup

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())

      remote_compute_node = self.requestRemoteNode(project, remote_project,
                                             owner_person)

      # and install some software on them (with same type)
      public_server_software = remote_server_software
      public_instance_type = remote_instance_type
      software_product, software_release, software_type = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.addAllocationSupply("for remote node", remote_compute_node, software_product,
                               software_release, software_type)
      self.tic()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(public_reference)
      workgroup = None
      destination_section = public_person
      if scenario == 'workgroup':
        self.login(sale_person.getUserId())
        workgroup = self.createWorkgroup(public_person, project=project,
                                         currency=currency)
        destination_section = workgroup

    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference(),
          # Remote workgroup is None always in this case.
          workgroup=workgroup)

      # now instantiate it on compute_node and set some nice connection dict
      self.simulateSlapgridCP(remote_server)
      self.login()

      # owner_person should have one Instance Tree created by alarm
      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=owner_person.getUid()
      )
      self.assertEqual(1, len(owner_instance_tree_list))
      owner_software_instance = owner_instance_tree_list[0].getSuccessorValue()
      self.assertEqual('Software Instance', owner_software_instance.getPortalType())
      self.assertEqual(
        remote_server.getRelativeUrl(),
        owner_software_instance.getAggregateValue().getParentValue().getRelativeUrl()
      )

      # public_person should have one Instance Tree
      public_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=destination_section.getUid()
      )
      self.assertEqual(1, len(public_instance_tree_list))

      self.assertEqual(
        '_remote_%s_%s' % (project.getReference(),
                           public_instance_tree_list[0].getSuccessorReference()),
        owner_software_instance.getTitle()
      )
      self.assertConnectionParameterFromInstance(owner_software_instance)

      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference(),
          workgroup=workgroup,
          connection_dict_to_check=owner_software_instance.getConnectionXmlAsDict())

      self.login(sale_person.getUserId())
      # Try now transfer to public person from the workgroup
      remote_node_change_request = remote_entity.Person_claimSlaposRemoteNode(
        remote_compute_node.getReference(), None)

      self.tic()
      self.login()
      self.assertEqual(remote_compute_node.getDestinationSection(),
                       remote_entity.getRelativeUrl())
      self.assertNotEqual(None, remote_node_change_request)
      self.assertEqual("Remote Node Change Request",
                          remote_node_change_request.getPortalType())
      self.assertEqual("invalidated",
                          remote_node_change_request.getSimulationState())

      owner_instance_tree_uid = owner_instance_tree_list[0].getUid()
      # remote_entity should have one Instance Tree
      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=remote_entity.getUid()
      )
      self.assertEqual(1, len(owner_instance_tree_list))
      self.assertEqual(owner_instance_tree_list[0].getUid(),
                       owner_instance_tree_uid)
      self.assertEqual(owner_instance_tree_list[0].getDestinationSection(),
                       remote_entity.getRelativeUrl())


      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=owner_person.getUid()
      )
      self.assertEqual(0, len(owner_instance_tree_list))

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 3 assignment request
    # 2 compute node
    # 1 credential request
    # 1 instance tree
    # 7 open sale order
    # 3 assignment
    # 3 simulation mvts
    # 1 remote node change request
    # 4 packing list
    # 2 sale trade condition
    # 1 software installation
    # 1 software instance
    # 1 software product
    # 1 subscription change request
    # 4 subscription request
    expected_amount = 36
    if scenario == 'remote_workgroup':
      # +1 assignment request
      # +1 sale trade condition
      # +1 workgroup
      expected_amount += 3
    self.assertRelatedObjectCount(remote_project, expected_amount)

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 4 assignment request
    # 1 remote node
    # 2 credential request
    # 1 instance tree
    # 4 open sale order
    # 4 assignment
    # 2 simulation mvt
    # 1 remote node change request
    # 2 packing list
    # 1 sale trade condition
    # 1 software instance
    # 1 software product
    # 2 subscription request
    expected_amount = 29
    if scenario == 'workgroup':
      # +1 assignment request
      # +1 sale trade condition
      # +1 workgroup
      expected_amount += 3
    self.assertRelatedObjectCount(project, expected_amount)

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.checkERP5StateBeforeExit()