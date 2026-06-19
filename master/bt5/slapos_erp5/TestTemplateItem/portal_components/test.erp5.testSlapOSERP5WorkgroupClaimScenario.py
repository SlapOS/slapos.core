# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2026 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSERP5WorkgroupClaimScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):
  pass


class TestSlapOSERP5WorkgroupClaimScenarion(TestSlapOSERP5WorkgroupClaimScenarioMixin):

  def test_workgroup_auto_claim_instance_scenario(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)
    self.tic()

    with PinnedDateTime(self, DateTime('2023/12/25')):
      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(owner_reference)

      # hooray, now it is time to create compute_nodes
      self.login(sale_person.getUserId())

      # create a default project
      project = self.addDefaultProject(person=owner_person, currency=currency)
      self.login(owner_person.getUserId())

      # and install some software on them
      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

    with PinnedDateTime(self, DateTime('2023/12/29')):
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(public_reference)

    with PinnedDateTime(self, DateTime('2024/01/01')):
      self.login(sale_person.getUserId())
      workgroup = self.createWorkgroup(None, project, currency)

    self.login()
    person_user_id = public_person.getUserId()
    software_release = public_server_software
    software_type = public_instance_type
    project_reference = project.getReference()

    public_instance_title = 'Public title %s' % self.generateNewId()
    with PinnedDateTime(self, DateTime('2024/01/10')):
      self.login(person_user_id)
      self.personRequestInstanceNotReady(
        software_release=software_release,
        software_type=software_type,
        partition_reference=public_instance_title,
        project_reference=project_reference
      )
      self.tic()
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)
      self.assertEqual(instance_tree.getDestinationSection(),
                       public_person.getRelativeUrl())

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.login(sale_person.getUserId())
      # Create a invitation token and invite the user.
      invitation_token = workgroup.Workgroup_addSlapOSAssignmentRequestInvitation(batch=1)
      self.tic()
      self.login(person_user_id)
      public_person.Person_acceptSlapOSInvitationToken(invitation_token,
                                                        accept_claim=1)
      self.tic()
      self.login()
      # Ensure assignment is closed after the user join the workgropu
      project_assignment = self.portal.portal_catalog.getResultValue(
        parent_uid=public_person.getUid(),
        portal_type='Assignment',
        destination_project__uid=project.getUid(),
        function__uid=self.portal.portal_categories.function.customer.getUid()
      )
      self.assertNotEqual(None, project_assignment)
      self.assertEqual('closed', project_assignment.getValidationState())

      # All fine until here.
      subscription_change_request = self.portal.portal_catalog.getResultValue(
        portal_type="Subscription Change Request",
        destination__uid=workgroup.getUid(),
        source_project__reference=project_reference
      )
      # instance is successfully claimed.
      self.assertEqual(instance_tree.getDestinationSection(),
                        workgroup.getRelativeUrl())
      self.assertEqual('invalidated',
        subscription_change_request.getSimulationState())

    self.checkServiceSubscriptionRequest(instance_tree)
    # Total of quantity should be zero
    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': False,
        'group_by_variation': False,
        'group_by_resource': True,
        'resource_uid': subscription_change_request.getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(1, len(inventory_list))
    self.assertAlmostEqual(0, inventory_list[0].total_quantity)

    # Seller only sold 1 month
    inventory_list_kw = {
        'node_uid': subscription_change_request.getSourceUid(),
        'group_by_section': False,
        'group_by_node': False,
        'group_by_variation': False,
        'group_by_resource': True,
        'resource_uid': subscription_change_request.getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(1, len(inventory_list))
    # 2 - 0.42 (13 days of 31) - 0.1 (3 days of 31) + 1 - 0.83 (24 days of 29)
    self.assertAlmostEqual(-1.65, inventory_list[0].total_quantity)

    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': True,
        'group_by_variation': True,
        'resource_uid': subscription_change_request.getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(3, len(inventory_list))

    # Ensure no unexpected object has been created
    # 4 assignment request
    # 1 credential request
    # 1 instance tree
    # 7 open sale order
    # 3 assignment
    # 4 simulation movement
    # 7 sale packing list / line
    # 3 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 1 software instance
    # 1 software product
    # 1 subscription change request
    # 2 subscription request
    self.assertRelatedObjectCount(project, 36)

    with PinnedDateTime(self, DateTime('2024/02/15')):
      self.checkERP5StateBeforeExit()

  def test_workgroup_auto_claim_instance_when_workgroup_join_project_scenario(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)
    self.tic()

    with PinnedDateTime(self, DateTime('2023/12/25')):
      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(owner_reference)

      # hooray, now it is time to create compute_nodes
      self.login(sale_person.getUserId())

      # create a default project
      project = self.addDefaultProject(
        person=owner_person, currency=currency)
      workgroup_project = self.portal.restrictedTraverse(self.addProject(
        person=owner_person, currency=currency))
      self.login(owner_person.getUserId())

      # and install some software on them
      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

    with PinnedDateTime(self, DateTime('2023/12/29')):
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(public_reference)
      public_reference2 = 'public-%s2' % self.generateNewId()
      public_person2 = self.joinSlapOS(public_reference2)

    with PinnedDateTime(self, DateTime('2024/01/01')):
      self.login(sale_person.getUserId())
      workgroup = self.createWorkgroup(None, workgroup_project, currency)
      organisation = self.portal.portal_catalog.getResultValue(
        portal_type='Organisation',
        title="%" + workgroup.getTitle() + "%",
        validation_state="validated"
      )
      self.assertNotEqual(organisation, None)

    self.login()
    person_user_id = public_person.getUserId()
    person2_user_id = public_person2.getUserId()
    software_release = public_server_software
    software_type = public_instance_type
    project_reference = project.getReference()

    public_instance_title = 'Public title %s' % self.generateNewId()
    public_instance_title2 = 'Public2 title %s' % self.generateNewId()
    with PinnedDateTime(self, DateTime('2024/01/10')):
      # public_person's instance
      self.login(person_user_id)
      self.personRequestInstanceNotReady(
        software_release=software_release,
        software_type=software_type,
        partition_reference=public_instance_title,
        project_reference=project_reference
      )
      self.tic()
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)
      self.assertEqual(instance_tree.getDestinationSection(),
                       public_person.getRelativeUrl())

      # public_person2's instance
      self.login(person2_user_id)
      self.personRequestInstanceNotReady(
        software_release=software_release,
        software_type=software_type,
        partition_reference=public_instance_title2,
        project_reference=project_reference
      )
      self.tic()
      instance_tree2 = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title2,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree2)
      self.assertEqual(instance_tree2.getDestinationSection(),
                       public_person2.getRelativeUrl())

    with PinnedDateTime(self, DateTime('2024/01/25')):
      for _person in [public_person, public_person2]:
        self.login(sale_person.getUserId())
        # Create a invitation token and invite the user.
        invitation_token = workgroup.Workgroup_addSlapOSAssignmentRequestInvitation(batch=1)
        self.tic()
        self.login(person_user_id)
        _person.Person_acceptSlapOSInvitationToken(invitation_token)

      self.tic()
      self.login()
      # Nothing changed
      self.assertEqual(instance_tree.getDestinationSection(),
                       public_person.getRelativeUrl())
      self.assertEqual(instance_tree2.getDestinationSection(),
                       public_person2.getRelativeUrl())

    with PinnedDateTime(self, DateTime('2024/02/25')):
      # Create a custom Trade Condition for Org + Workgroup into Default Project
      instance_tree_trade_condition = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Trade Condition',
        trade_condition_type__uid=self.portal.portal_categories.trade_condition_type.instance_tree.getUid(),
        price_currency__uid=currency.getUid(),
        validation_state='validated',
        default_source_project_uid = project.getUid()
      )
      dedicated_trade_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition',
        title='%s dedicated %s' % (instance_tree_trade_condition.getTitle(), workgroup.getTitle()),
        source_project=instance_tree_trade_condition.getSourceProject(),
        destination_value=workgroup,
        destination_section_value=organisation,
        specialise_value=instance_tree_trade_condition,
        price_currency=instance_tree_trade_condition.getPriceCurrency(),
        trade_condition_type=instance_tree_trade_condition.getTradeConditionType()
      )
      dedicated_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate()
      self.tic()

      self.login(sale_person.getUserId())
      # Create one invitation token, as Project_addSlapOSAssignmentRequestInvitation
      invitation_token = self.portal.invitation_token_module.newContent(
        portal_type="Invitation Token",
        follow_up_value=project,
        function_value=self.portal.portal_categories.function.customer
      )
      invitation_token.validate()
      invitation_token = invitation_token.getId()
      self.tic()

      # Now accept token to make workgroup join the project and trigger everything
      workgroup.Person_acceptSlapOSInvitationToken(invitation_token)

      self.tic()
      self.login()
      # All fine until here.
      subscription_change_request_list = self.portal.portal_catalog(
        portal_type="Subscription Change Request",
        destination__uid=workgroup.getUid(),
        source_project__reference=project_reference
      )
      # instance is successfully claimed.
      self.assertEqual(2, len(subscription_change_request_list))
      self.assertEqual('invalidated',
        subscription_change_request_list[0].getSimulationState())
      self.assertEqual('invalidated',
        subscription_change_request_list[1].getSimulationState())

      self.assertEqual(instance_tree.getDestinationSection(),
                        workgroup.getRelativeUrl())
      self.assertEqual(instance_tree2.getDestinationSection(),
                        workgroup.getRelativeUrl())

    self.checkServiceSubscriptionRequest(instance_tree)
    # Total of quantity should be zero
    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': False,
        'group_by_variation': False,
        'group_by_resource': True,
        'resource_uid': subscription_change_request_list[0].getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(1, len(inventory_list))
    self.assertAlmostEqual(0, inventory_list[0].total_quantity)

    # Seller only sold 1 month
    inventory_list_kw = {
        'node_uid': subscription_change_request_list[0].getSourceUid(),
        'group_by_section': False,
        'group_by_node': False,
        'group_by_variation': False,
        'group_by_resource': True,
        'resource_uid': subscription_change_request_list[0].getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(1, len(inventory_list))
    # 2 - 0.42 (13 days of 31) - 0.1 (3 days of 31) + 1 - 0.83 (24 days of 29)
    # -1.65 * 2 (instances number) == -3.3
    self.assertAlmostEqual(-1.65*2, inventory_list[0].total_quantity)

    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': True,
        'group_by_variation': True,
        'resource_uid': subscription_change_request_list[0].getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEqual(4, len(inventory_list))

    # Ensure no unexpected object has been created
    # 7 assignment request
    # 2 credential request
    # 2 instance tree
    # 1 invitation token
    # 13 open sale order
    # 4 assignment
    # 7 simulation movement
    # 13 sale packing list / line
    # 2 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 2 software instance
    # 1 software product
    # 2 subscription change request
    # 5 subscription request
    # 1 workgroup
    self.assertRelatedObjectCount(project, 60)

    with PinnedDateTime(self, DateTime('2024/02/15')):
      self.checkERP5StateBeforeExit()


  def test_workgroup_auto_claim_instance_from_remote_node_when_user_join_workgroup_scenario(self):
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

    with PinnedDateTime(self, DateTime('2024/01/01')):
      self.login(sale_person.getUserId())
      workgroup = self.createWorkgroup(None, project, currency)
      organisation = self.portal.portal_catalog.getResultValue(
        portal_type='Organisation',
        title="%" + workgroup.getTitle() + "%",
        validation_state="validated"
      )
      self.assertNotEqual(organisation, None)

    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference(),
          # Remote workgroup is None always in this case.
          workgroup=None)

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
        destination_section__uid=public_person.getUid()
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
          workgroup=None,
          connection_dict_to_check=owner_software_instance.getConnectionXmlAsDict())

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.login()
      # Create a custom Trade Condition for Org + Workgroup into Default Project
      instance_tree_trade_condition = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Trade Condition',
        trade_condition_type__uid=self.portal.portal_categories.trade_condition_type.instance_tree.getUid(),
        price_currency__uid=currency.getUid(),
        validation_state='validated',
        default_source_project_uid = project.getUid()
      )
      dedicated_trade_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition',
        title='%s dedicated %s' % (instance_tree_trade_condition.getTitle(), workgroup.getTitle()),
        source_project=instance_tree_trade_condition.getSourceProject(),
        destination_value=workgroup,
        destination_section_value=organisation,
        specialise_value=instance_tree_trade_condition,
        price_currency=instance_tree_trade_condition.getPriceCurrency(),
        trade_condition_type=instance_tree_trade_condition.getTradeConditionType()
      )
      dedicated_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate()
      self.tic()

      self.login(sale_person.getUserId())

      ###############################################################
      # Workgroup joins the project BEFORE User joins the workgroup
      # in this case, remote node is not changes.
      ##############################################################
      # Create one invitation token, as Project_addSlapOSAssignmentRequestInvitation
      invitation_token = self.portal.invitation_token_module.newContent(
        portal_type="Invitation Token",
        follow_up_value=remote_project,
        function_value=self.portal.portal_categories.function.customer
      )
      invitation_token.validate()
      invitation_token = invitation_token.getId()
      self.tic()

      # Now accept token to make workgroup join the project (nothing is trigger)
      workgroup.Person_acceptSlapOSInvitationToken(invitation_token)

      self.tic()
      remote_node_change_request = self.portal.portal_catalog(
        portal_type="Remote Node Change Request",
        destination_section__uid=workgroup.getUid())

      self.assertEqual(len(remote_node_change_request), 0)

      #####################################################################
      # Now the user joins the workgroup, leading to auto claim be trigger
      #####################################################################

      # Create a invitation token and invite the user.
      invitation_token = workgroup.Workgroup_addSlapOSAssignmentRequestInvitation(batch=1)
      self.tic()
      self.login(public_person.getUserId())
      assignment_request = remote_public_person.Person_acceptSlapOSInvitationToken(
          invitation_token, accept_claim=1, batch=1)

      self.assertEqual(assignment_request.getSimulationState(), 'draft')
      self.tic()
      self.assertEqual(assignment_request.getSimulationState(), 'validated')
      self.login()

      # Ensure now, with the join a Remote Node Change Request is created
      remote_node_change_request = self.portal.portal_catalog(
        portal_type="Remote Node Change Request",
        simulation_state="invalidated",
        destination_section__uid=workgroup.getUid())

      self.assertEqual(len(remote_node_change_request), 1)
      owner_instance_tree_uid = owner_instance_tree_list[0].getUid()
      # remote_entity should have one Instance Tree
      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=workgroup.getUid()
      )
      self.assertEqual(1, len(owner_instance_tree_list))
      self.assertEqual(owner_instance_tree_list[0].getUid(),
                       owner_instance_tree_uid)
      self.assertEqual(owner_instance_tree_list[0].getDestinationSection(),
                       workgroup.getRelativeUrl())

      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=owner_person.getUid()
      )
      self.assertEqual(0, len(owner_instance_tree_list))

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 4 assignment request
    # 2 compute node
    # 1 credential request
    # 1 event
    # 1 instance tree
    # 4 open sale order
    # 1 invitation token
    # 3 assignment
    # 2 simulation mvts
    # 1 remote node change request
    # 3 packing list
    # 1 sale trade condition
    # 1 subscription change request
    # 3 subscription request
    # 1 workgroup
    expected_amount = 35
    self.assertRelatedObjectCount(remote_project, expected_amount)

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 4 assignment request
    # 1 remote node
    # 1 credential request
    # 1 instance tree
    # 4 open sale order
    # 3 assignment
    # 1 remote node change request
    # 2 simulation mvt
    # 1 remote node
    # 2 packing list
    # 3 sale trade condition
    # 1 software instance
    # 1 software product
    # 2 subscription request
    # 1 workgroup
    expected_amount = 30
    self.assertRelatedObjectCount(project, expected_amount)


  def test_workgroup_auto_claim_instance_from_remote_node_when_workgroup_join_remote_project_scenario(self):
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

    with PinnedDateTime(self, DateTime('2024/01/01')):
      self.login(sale_person.getUserId())
      workgroup = self.createWorkgroup(None, project, currency)
      organisation = self.portal.portal_catalog.getResultValue(
        portal_type='Organisation',
        title="%" + workgroup.getTitle() + "%",
        validation_state="validated"
      )
      self.assertNotEqual(organisation, None)

    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference(),
          # Remote workgroup is None always in this case.
          workgroup=None)

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
        destination_section__uid=public_person.getUid()
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
          workgroup=None,
          connection_dict_to_check=owner_software_instance.getConnectionXmlAsDict())

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.login()
      # Create a custom Trade Condition for Org + Workgroup into Default Project
      instance_tree_trade_condition = self.portal.portal_catalog.getResultValue(
        portal_type='Sale Trade Condition',
        trade_condition_type__uid=self.portal.portal_categories.trade_condition_type.instance_tree.getUid(),
        price_currency__uid=currency.getUid(),
        validation_state='validated',
        default_source_project_uid = project.getUid()
      )
      dedicated_trade_condition = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition',
        title='%s dedicated %s' % (instance_tree_trade_condition.getTitle(), workgroup.getTitle()),
        source_project=instance_tree_trade_condition.getSourceProject(),
        destination_value=workgroup,
        destination_section_value=organisation,
        specialise_value=instance_tree_trade_condition,
        price_currency=instance_tree_trade_condition.getPriceCurrency(),
        trade_condition_type=instance_tree_trade_condition.getTradeConditionType()
      )
      dedicated_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate()
      self.tic()

      #####################################################################
      # The remote user joins the Workgroup, since the Workgroup is not
      # a member of remote project, remote instance is not claimed and 
      # remote node is intact.
      #####################################################################

      self.login(sale_person.getUserId())

      # Create a invitation token and invite the user.
      invitation_token = workgroup.Workgroup_addSlapOSAssignmentRequestInvitation(batch=1)
      self.tic()
      self.login(remote_public_person.getUserId())
      assignment_request = remote_public_person.Person_acceptSlapOSInvitationToken(
          invitation_token, batch=1)

      self.assertEqual(assignment_request.getSimulationState(), 'submitted')
      self.tic()
      self.assertEqual(assignment_request.getSimulationState(), 'validated')

      remote_node_change_request = self.portal.portal_catalog(
        portal_type="Remote Node Change Request",
        destination_section__uid=workgroup.getUid())

      self.assertEqual(len(remote_node_change_request), 0)

      self.login(sale_person.getUserId())

      ###############################################################
      # Workgroup joins the remote project AFTER User joins the workgroup
      # in this case, remote node is changed.
      ##############################################################

      # Create one invitation token, as Project_addSlapOSAssignmentRequestInvitation
      invitation_token = self.portal.invitation_token_module.newContent(
        portal_type="Invitation Token",
        follow_up_value=remote_project,
        function_value=self.portal.portal_categories.function.customer
      )
      invitation_token.validate()
      invitation_token = invitation_token.getId()
      self.tic()

      assignment_request = workgroup.Person_acceptSlapOSInvitationToken(
        invitation_token, batch=1)

      self.assertEqual(assignment_request.getSimulationState(), 'submitted')
      self.tic()
      self.assertEqual(assignment_request.getSimulationState(), 'validated')
      self.login()

      # Ensure now, with the join a Remote Node Change Request is created
      remote_node_change_request = self.portal.portal_catalog(
        portal_type="Remote Node Change Request",
        simulation_state="invalidated",
        destination_section__uid=workgroup.getUid())

      self.assertEqual(len(remote_node_change_request), 1)
      owner_instance_tree_uid = owner_instance_tree_list[0].getUid()
      # remote_entity should have one Instance Tree
      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=workgroup.getUid()
      )
      self.assertEqual(1, len(owner_instance_tree_list))
      self.assertEqual(owner_instance_tree_list[0].getUid(),
                       owner_instance_tree_uid)
      self.assertEqual(owner_instance_tree_list[0].getDestinationSection(),
                       workgroup.getRelativeUrl())

      owner_instance_tree_list = self.portal.portal_catalog(
        portal_type='Instance Tree',
        destination_section__uid=owner_person.getUid()
      )
      self.assertEqual(0, len(owner_instance_tree_list))

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 4 assignment request
    # 2 compute node
    # 1 credential request
    # 1 event
    # 1 instance tree
    # 4 open sale order
    # 1 invitation token
    # 3 assignment
    # 2 simulation mvts
    # 1 remote node change request
    # 3 packing list
    # 2 sale trade condition
    # 1 subscription change request
    # 1 instance tree module
    # 1 software product
    # 3 subscription request
    # 1 workgroup
    expected_amount = 35
    self.assertRelatedObjectCount(remote_project, expected_amount)

    # Ensure no unexpected object has been created
    # 3 allocation supply
    # 4 assignment request
    # 1 remote node
    # 1 credential request
    # 1 instance tree
    # 4 open sale order
    # 3 assignment
    # 1 remote node change request
    # 2 simulation mvt
    # 1 remote node
    # 2 packing list
    # 3 sale trade condition
    # 1 software instance
    # 1 software product
    # 2 subscription request
    # 1 workgroup
    expected_amount = 30
    self.assertRelatedObjectCount(project, expected_amount)


  def test_workgroup_cannot_join_due_instance_name_confict_scenario(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)
    self.tic()

    with PinnedDateTime(self, DateTime('2023/12/25')):
      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      owner_person = self.joinSlapOS(owner_reference)

      # hooray, now it is time to create compute_nodes
      self.login(sale_person.getUserId())

      # create a default project
      project = self.addDefaultProject(person=owner_person, currency=currency)
      self.login(owner_person.getUserId())

      # and install some software on them
      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

    with PinnedDateTime(self, DateTime('2023/12/29')):
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(public_reference)

      public2_reference = 'public2-%s' % self.generateNewId()
      public_person2 = self.joinSlapOS(public2_reference)

    with PinnedDateTime(self, DateTime('2024/01/01')):
      workgroup = self.createWorkgroup(public_person, project, currency)
      self.login()
      self.tic()
      # Ensure assignment is closed after the user join the workgropu
      project_assignment = self.portal.portal_catalog.getResultValue(
        parent_uid=public_person.getUid(),
        portal_type='Assignment',
        destination_project__uid=project.getUid(),
        function__uid=self.portal.portal_categories.function.customer.getUid()
      )
      self.assertNotEqual(None, project_assignment)
      self.assertEqual('closed',
         project_assignment.getValidationState())


    self.login()
    person_user_id = public_person.getUserId()
    person2_user_id = public_person2.getUserId()
    software_release = public_server_software
    software_type = public_instance_type
    project_reference = project.getReference()

    public_instance_title = 'Public title %s' % self.generateNewId()
    request_kw = {
      'software_release' : software_release,
      'software_type' : software_type,
      'partition_reference' : public_instance_title,
      'project_reference' : project_reference
    }

    with PinnedDateTime(self, DateTime('2024/01/10')):
      self.login(person_user_id)
      self.personRequestInstanceNotReady(**request_kw)
      self.tic()
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)
      self.assertEqual(instance_tree.getDestinationSection(),
                       workgroup.getRelativeUrl())

      self.login(person2_user_id)
      self.personRequestInstanceNotReady(**request_kw)
      self.tic()
      instance_tree2 = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)
      self.assertEqual(instance_tree2.getDestinationSection(),
        public_person2.getRelativeUrl())

    with PinnedDateTime(self, DateTime('2024/01/20')):
      self.login(sale_person.getUserId())
      # Create a invitation token and invite the user.
      invitation_token = workgroup.Workgroup_addSlapOSAssignmentRequestInvitation(batch=1)
      self.tic()
      self.login(public_person2.getUserId())
      public_person2.Person_acceptSlapOSInvitationToken(
        # Accept claim but it might ignore the claim due conflict
        invitation_token, accept_claim=1)
      self.tic()

      self.login()
      # Ensure assignment is open for the project (nothing is cancelled)
      project_assignment = self.portal.portal_catalog.getResultValue(
        parent_uid=public_person2.getUid(),
        portal_type='Assignment',
        destination_project__uid=project.getUid(),
        function__uid=self.portal.portal_categories.function.customer.getUid()
      )
      # Assignment is not closed
      self.assertNotEqual(None, project_assignment)
      self.assertEqual('open',
         project_assignment.getValidationState())

      # Ensure assignment assignment to workgroup was not created
      workgroup_assignment = self.portal.portal_catalog.getResultValue(
        parent_uid=public_person2.getUid(),
        portal_type='Assignment',
        destination__uid=workgroup.getUid()
      )
      self.assertEqual(None, workgroup_assignment)

      # Ensure assignment assignment to workgroup was not created
      workgroup_assignment_request = self.portal.portal_catalog.getResultValue(
        destination_decision__uid=public_person2.getUid(),
        portal_type='Assignment Request',
        destination__uid=workgroup.getUid()
      )
      self.assertNotEqual(None, workgroup_assignment_request)
      self.assertEqual('draft',
         workgroup_assignment_request.getSimulationState())

