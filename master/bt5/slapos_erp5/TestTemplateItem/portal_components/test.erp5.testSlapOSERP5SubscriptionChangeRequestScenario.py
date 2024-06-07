# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSSubscriptionChangeRequestScenarioMixin(TestSlapOSVirtualMasterScenarioMixin):
  pass


class TestSlapOSSubscriptionChangeRequestScenario(TestSlapOSSubscriptionChangeRequestScenarioMixin):

  def test_subscription_change_request_change_instance_destination_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.tic()

    self.logout()

    with PinnedDateTime(self, DateTime('2024/01/25')):
      # lets join as slapos administrator, which will own few compute_nodes
      owner_reference = 'owner-%s' % self.generateNewId()
      self.joinSlapOS(self.web_site, owner_reference)

      self.login()
      owner_person = self.portal.portal_catalog.getResultValue(
        portal_type="ERP5 Login",
        reference=owner_reference).getParentValue()
      #owner_person.setCareerSubordinationValue(seller_organisation)

      self.tic()

      # hooray, now it is time to create compute_nodes
      self.logout()
      self.login(sale_person.getUserId())

      # create a default project
      project_relative_url = self.addProject(person=owner_person, currency=currency)

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

      self.logout()
      self.login(owner_person.getUserId())

      # and install some software on them
      public_server_software = self.generateNewSoftwareReleaseUrl()
      public_instance_type = 'public type'

      self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      # join as the another visitor and request software instance on public
      # compute_node
      self.logout()

    with PinnedDateTime(self, DateTime('2023/12/29')):
      public_reference = 'public-%s' % self.generateNewId()
      self.joinSlapOS(self.web_site, public_reference)
    with PinnedDateTime(self, DateTime('2024/02/01')):
      public_reference2 = 'public2-%s' % self.generateNewId()
      self.joinSlapOS(self.web_site, public_reference2)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()
    public_person2 = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference2).getParentValue()

    person_user_id = public_person.getUserId()
    software_release = public_server_software
    software_type = public_instance_type
    project_reference = project.getReference()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.login(person_user_id)

    with PinnedDateTime(self, DateTime('2024/01/10')):
      self.personRequestInstanceNotReady(
        software_release=software_release,
        software_type=software_type,
        partition_reference=public_instance_title,
        project_reference=project_reference
      )
      self.tic()

      # XXX search only for this user
      instance_tree = self.portal.portal_catalog.getResultValue(
        portal_type="Instance Tree",
        title=public_instance_title,
        follow_up__reference=project_reference
      )
      self.checkServiceSubscriptionRequest(instance_tree)
      self.tic()

    with PinnedDateTime(self, DateTime('2024/02/25')):
      self.login(sale_person.getUserId())
      subscription_change_request = public_person2.Person_claimSlaposItemSubscription(
        instance_tree.getReference(),
        None
      )

      self.tic()
      self.logout()
      self.login()
      self.assertEquals(instance_tree.getDestinationSection(),
                        public_person2.getRelativeUrl())


    # Total of quantity should be zero
    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': False,
        'group_by_variation': False,
        'group_by_resource': True,
        'resource_uid': subscription_change_request.getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEquals(1, len(inventory_list))
    self.assertEquals(0, inventory_list[0].total_quantity)

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
    self.assertEquals(1, len(inventory_list))
    # 2 - 0.42 (13 days of 31) - 0.1 (3 days of 31) + 1 - 0.83 (24 days of 29)
    self.assertAlmostEquals(-1.65, inventory_list[0].total_quantity)

    inventory_list_kw = {
        'group_by_section': False,
        'group_by_node': True,
        'group_by_variation': True,
        'resource_uid': subscription_change_request.getResourceUid(),
    }
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**inventory_list_kw)
    self.assertEquals(3, len(inventory_list))

    # tracking_list = instance_tree.Item_getTrackingList()
    # self.assertEquals(2, len(tracking_list))

    # XXX TODO self.assertEquals(None, self.portal.portal_simulation.getInventoryList())

    # Ensure no unexpected object has been created
    # 2 credential request
    # 1 instance tree
    # 7 open sale order
    # 4 assignment
    # 4 simulation movement
    # 7 sale packing list / line
    # 2 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 1 software instance
    # 1 software product
    # 1 subscription change request
    # 2 subscription request
    self.assertRelatedObjectCount(project, 32)

    with PinnedDateTime(self, DateTime('2024/02/15')):
      self.checkERP5StateBeforeExit()

