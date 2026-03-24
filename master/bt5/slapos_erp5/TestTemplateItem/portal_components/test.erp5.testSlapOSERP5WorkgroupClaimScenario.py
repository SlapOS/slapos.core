# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
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
    # 4 assignment
    # 4 simulation movement
    # 7 sale packing list / line
    # 3 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 1 software instance
    # 1 software product
    # 1 subscription change request
    # 2 subscription request
    self.assertRelatedObjectCount(project, 37)

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
    # 5 assignment request
    # 2 credential request
    # 2 instance tree
    # 1 invitation token
    # 13 open sale order
    # 4 assignment
    # 7 simulation movement
    # 13 sale packing list / line
    # 3 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 2 software instance
    # 1 software product
    # 2 subscription change request
    # 5 subscription request
    self.assertRelatedObjectCount(project, 61)

    with PinnedDateTime(self, DateTime('2024/02/15')):
      self.checkERP5StateBeforeExit()


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
      # Ensure assignment is closed after the user join the workgropu
      project_assignment = self.portal.portal_catalog.getResultValue(
        parent_uid=public_person.getUid(),
        portal_type='Assignment',
        destination_project__uid=project.getUid(),
        function__uid=self.portal.portal_categories.function.production.getUid()
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

