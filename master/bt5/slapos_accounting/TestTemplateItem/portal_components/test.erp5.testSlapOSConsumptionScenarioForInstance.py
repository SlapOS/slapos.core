# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from erp5.component.module.DateUtils import addToDate


from DateTime import DateTime

class testSlapOSConsumptionScenarioForInstance(TestSlapOSVirtualMasterScenarioMixin):


  def bootstrapConsumptionScenarioTest(self):
    currency, _, _, sale_person, _ = self.bootstrapVirtualMasterTest()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    project_owner_reference = 'project-%s' % self.generateNewId()
    project_owner_person = self.joinSlapOS(
      self.web_site, project_owner_reference)

    self.login()
    self.tic()
    self.logout()
    self.login(sale_person.getUserId())

    project_relative_url = self.addProject(
      is_accountable=True,
      person=project_owner_person,
      currency=currency)

    project = self.portal.restrictedTraverse(project_relative_url)
    self.logout()
    self.login()

    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % project_relative_url
      ]
    )

    public_server_software = self.generateNewSoftwareReleaseUrl()
    public_instance_type = 'public type'

    software_product, release_variation, type_variation = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.tic()

    self.logout()
    self.login(sale_person.getUserId())

    sale_supply = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Supply',
      source_project__uid=project.getUid()
    )
    sale_supply.searchFolder(
      portal_type='Sale Supply Line',
      resource__relative_url="service_module/slapos_compute_node_subscription"
    )[0].edit(base_price=99)
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      base_price=9,
      resource_value=software_product
    )

    # Do like this for now, change later
    sale_supply.newContent(
      portal_type='Sale Supply Line',
      base_price = 5,
      resource_value = self.portal.service_module.instance_consumption
    )
    sale_supply.validate()

    self.tic()
    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    owner_person = self.joinSlapOS(self.web_site, owner_reference)

    self.login()

    # first slapos administrator assignment can only be created by
    # the erp5 manager
    self.addProjectProductionManagerAssignment(owner_person, project)
    self.tic()

    # hooray, now it is time to create compute_nodes
    self.login(owner_person.getUserId())

    public_server_title = 'Public Server for %s' % owner_reference
    public_server_id = self.requestComputeNode(public_server_title, project.getReference())
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=public_server_id)
    self.setAccessToMemcached(public_server)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)
    public_server.generateCertificate()

    self.addAllocationSupply("for compute node", public_server, software_product,
                               release_variation, type_variation)

    # and install some software on them
    self.supplySoftware(public_server, public_server_software)

    # format the compute_nodes
    self.formatComputeNode(public_server)

    self.logout()

    # Pay deposit to validate virtual master + one computer
    deposit_amount = 42.0 + 99.0
    self.login(project_owner_person.getUserId())
    ledger = self.portal.portal_categories.ledger.automated

    outstanding_amount_list = project_owner_person.Entity_getOutstandingDepositAmountList(
        currency.getUid(), ledger_uid=ledger.getUid())
    amount = sum([i.total_price for i in outstanding_amount_list])
    self.assertEqual(amount, deposit_amount)

    # Ensure to pay from the website
    outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
    outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

    self.tic()
    self.logout()
    self.login()
    payment_transaction = self.portal.portal_catalog.getResultValue(
      portal_type="Payment Transaction",
      destination_section_uid=project_owner_person.getUid(),
      simulation_state="started"
    )
    self.assertEqual("deposit",
      payment_transaction.getSpecialiseValue().getTradeConditionType())
    # payzen/wechat or accountant will only stop the payment
    payment_transaction.stop()
    self.tic()
    self.assertNotEqual(None,
                    payment_transaction.receivable.getGroupingReference(None))
    self.login(project_owner_person.getUserId())

    amount = sum([i.total_price for i in project_owner_person.Entity_getOutstandingDepositAmountList(
        currency.getUid(), ledger_uid=ledger.getUid())])
    self.assertEqual(0, amount)
    self.logout()

    return project, currency, owner_person, project_owner_person, public_server, \
             public_instance_type, public_server_software, software_product, \
             type_variation, sale_supply, sale_person


  def test_instance_consumption_scenario(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software, _,  \
        _, _, _ = self.bootstrapConsumptionScenarioTest()

      self.logout()

      # join as the another visitor and request software instance on public
      # compute_node
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.login()

    with PinnedDateTime(self, DateTime('2024/12/17 01:01')):
      # Simulate access from compute_node, to open the capacity scope
      self.login()
      self.simulateSlapgridSR(public_server)

      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          9.0, currency)
    with PinnedDateTime(self, DateTime('2024/12/17 01:02')):
      public_instance_title2 = 'Public title %s 2' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title2,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          10.8, currency)


    with PinnedDateTime(self, DateTime('2025/01/18 01:00')):
      self.login()
      # update open sale order of project
      self.portal.portal_alarms.update_open_order_simulation.activeSense()
      self.tic()
      #XXXX we should not reply to this
      #XXXX we need something when invalidate instance, the correct consumption delivery can be create
      self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_from_software_slave_instance.activeSense()
      self.tic()

      # Search used partition
      instance_tree = self.portal.portal_catalog.getResultValue(
        title=public_instance_title, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      instance_tree2 = self.portal.portal_catalog.getResultValue(
        title=public_instance_title2, portal_type='Instance Tree',
        default_destination_section_uid=public_person.getUid())

      self.assertNotEqual(None, instance_tree)
      software_instance = instance_tree.getSuccessorValue()
      partition = software_instance.getAggregateValue()
      self.assertEqual(partition.getParentValue(), public_server)

      self.assertNotEqual(None, instance_tree2)
      software_instance2 = instance_tree2.getSuccessorValue()
      partition2 = software_instance2.getAggregateValue()
      self.assertEqual(partition2.getParentValue(), public_server)

      consumption_delivery = software_instance.getCausalityRelatedValue(portal_type='Consumption Delivery')
      consumption_delivery2 = software_instance2.getCausalityRelatedValue(portal_type='Consumption Delivery')
      self.assertTrue(consumption_delivery is not None)
      self.assertTrue(consumption_delivery2 is not None)

      self.login(owner_person.getUserId())
      # Unallocate and destroy the instance the instances
      #XXXXXXXXXXXXXXXX how can we assume that when unallocated, the related consumption delivery is already created
      self.checkInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type, public_server,
          project.getReference())

      self.checkInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title2,
          public_server_software, public_instance_type, public_server,
          project.getReference())

      # and uninstall some software on them
      self.logout()
      self.login(owner_person.getUserId())
      self.supplySoftware(public_server,
                          public_server_software,
                          state='destroyed')

      self.logout()
      # Uninstall from compute_node
      self.login()
      self.tic()


    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(
      mirror_section_uid=public_person.getUid())

    # 9    deposite
    # 9    deposite
    # 21.6 instance
    # 10.8 deposite
    # 10.8 deposite
    for transaction in transaction_list:
      self.logMessage(transaction.getRelativeUrl())

    self.assertEqual(len(transaction_list), 5)
    self.assertSameSet(
      [round(x.total_price, 2) for x in transaction_list],
      [9.0, -9.0, 21.6, -10.8, 10.8],
      [round(x.total_price, 2) for x in transaction_list]
    )
    self.assertEqual(
      consumption_delivery.getCausalityRelatedValue(portal_type='Sale Invoice Transaction'),
      consumption_delivery2.getCausalityRelatedValue(portal_type='Sale Invoice Transaction')
    )
    self.login()
    #XXXXXXXXXXX wrong
    # Ensure no unexpected object has been created
    # 4 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 2 consumption delivery
    # 2 consumption document
    # 2 consumption supply
    # 2 credential request
    # 3 event
    # 2 instance tree
    # 9 open sale order / line
    # 5 (can reduce to 2) assignment
    # 65 simulation mvt
    # 6 packing list / line
    # 4 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 4 subscription requests
    self.assertRelatedObjectCount(project, 113)

    self.checkERP5StateBeforeExit()




  def test_software_instance_validate(self):
    instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
    self.tic()
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
      instance,
      'Base_generateConsumptionDeliveryForValidatedInstance'
    )

    self.portal.portal_workflow._jumpToStateFor(instance, 'validated')
    instance.reindexObject()
    self.tic()

    self._test_alarm(
      self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
      instance,
      'Base_generateConsumptionDeliveryForValidatedInstance'
    )


  def test_software_instance_invalidate(self):
    now = DateTime()

    with PinnedDateTime(self, now):
      instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
      self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
      self.tic()

    with PinnedDateTime(self, addToDate(now, minute=1)):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      # To clean last edit comment
      instance.edit()
      self.tic()

    with PinnedDateTime(self, addToDate(now, minute=2)):
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )





  def test_slave_instance_consumption_scenario(self):
    with PinnedDateTime(self, DateTime('2024/12/17')):
      project, currency, owner_person, _, public_server, public_instance_type, \
        public_server_software, _,  \
        _, sale_supply, _ = self.bootstrapConsumptionScenarioTest()


      self.logout()
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.logout()
      shared_public_reference = 'shared_public-%s' % self.generateNewId()
      shared_public_person = self.joinSlapOS(self.web_site, shared_public_reference)

      self.login()

    with PinnedDateTime(self, DateTime('2024/02/17 00:05')):
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkInstanceAllocationWithDeposit(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          public_server, project.getReference(),
          9.0, currency)

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())
      instance_node_title = 'Shared Instance for %s' % owner_person.getTitle()
      # Convert the Software Instance into an Instance Node
      # to explicitely mark it as accepting Slave Instance
      software_instance = self.portal.portal_catalog.getResultValue(
          portal_type='Software Instance', title=public_instance_title)
      instance_node = self.addInstanceNode(instance_node_title, software_instance)

      slave_server_software = self.generateNewSoftwareReleaseUrl()
      slave_instance_type = 'slave type'
      software_product, software_release, software_type = self.addSoftwareProduct(
        'share product', project, slave_server_software, slave_instance_type
      )
      self.addAllocationSupply("for instance node", instance_node, software_product,
                               software_release, software_type)



      self.login()
      #XXXXXXXXX
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=9,
        resource_value=software_product
      )
      self.tic()
      slave_instance_title = 'Slave title %s' % self.generateNewId()
      self.checkSlaveInstanceAllocationWithDeposit(shared_public_person.getUserId(),
          shared_public_reference, slave_instance_title,
          slave_server_software, slave_instance_type,
          public_server, project.getReference(),
          9.0, currency)

      self.login(owner_person.getUserId())

      # and the instances
      self.checkSlaveInstanceUnallocation(shared_public_person.getUserId(),
          shared_public_reference, slave_instance_title,
          slave_server_software, slave_instance_type, public_server,
          project.getReference())

      # and uninstall some software on them
      self.logout()
      self.login(owner_person.getUserId())
      self.supplySoftware(public_server, public_server_software,
                          state='destroyed')

      self.logout()
      # Uninstall from compute_node
      self.login()
      self.simulateSlapgridSR(public_server)

    self.tic()

    self.login()

    self.checkERP5StateBeforeExit()



  def test_remote_instance_consumption_scenario(self):

    with PinnedDateTime(self, DateTime('2024/02/17')):
      remote_project, currency, owner_person, _, remote_server, remote_instance_type, \
        remote_server_software, _,  \
        _, sale_supply, sale_person = self.bootstrapConsumptionScenarioTest()

      # some preparation
      self.logout()
      remote_public_reference = 'remote-public-%s' % self.generateNewId()
      remote_public_person = self.joinSlapOS(self.web_site, remote_public_reference)

      self.login()

      ####################################
      # Create a local project
      ####################################
      self.logout()
      self.login(sale_person.getUserId())
      # create a default project
      project_relative_url = self.addProject(person=remote_public_person, currency=currency)

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

      owner_person = remote_public_person
      self.logout()

      # hooray, now it is time to create compute_nodes
      self.login(owner_person.getUserId())

      # Pay deposit to validate virtual master + one computer
      deposit_amount = 42.0
      ledger = self.portal.portal_categories.ledger.automated

      outstanding_amount_list = owner_person.Entity_getOutstandingDepositAmountList(
          currency.getUid(), ledger_uid=ledger.getUid())
      amount = sum([i.total_price for i in outstanding_amount_list])
      self.assertEqual(amount, deposit_amount)

      # Ensure to pay from the website
      outstanding_amount = self.web_site.restrictedTraverse(outstanding_amount_list[0].getRelativeUrl())
      outstanding_amount.Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect()

      self.tic()
      self.login()
      payment_transaction = self.portal.portal_catalog.getResultValue(
        portal_type="Payment Transaction",
        destination_section_uid=owner_person.getUid(),
        simulation_state="started"
      )
      self.assertEqual("deposit",
        payment_transaction.getSpecialiseValue().getTradeConditionType())
      # payzen/wechat or accountant will only stop the payment
      payment_transaction.stop()
      self.login(owner_person.getUserId())

      remote_compute_node = self.requestRemoteNode(project, remote_project,
                                             remote_public_person)

      # and install some software on them
      public_server_software = remote_server_software

      #software_product, release_variation, type_variation = self.addSoftwareProduct(
      public_instance_type = remote_instance_type
      software_product, software_release, software_type = self.addSoftwareProduct(
        "instance product", project, public_server_software, public_instance_type
      )

      self.addAllocationSupply("for remote node", remote_compute_node, software_product,
                               software_release, software_type)
      self.tic()

      # join as the another visitor and request software instance on public
      # compute_node
      self.logout()
      public_reference = 'public-%s' % self.generateNewId()
      public_person = self.joinSlapOS(self.web_site, public_reference)

      self.login()
      #XXXXXXXXX
      sale_supply.newContent(
        portal_type="Sale Supply Line",
        base_price=9,
        resource_value=software_product
      )
      sale_supply.setSourceProjectValueList(sale_supply.getSourceProjectValueList() + [project])
      self.tic()

      self.login()

    with PinnedDateTime(self, DateTime('2024/02/17 01:01')):
      public_instance_title = 'Public title %s' % self.generateNewId()
      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference())

      # XXX Do this for every scenario tests
      self.logout()
      self.tic()
      # now instantiate it on compute_node and set some nice connection dict
      self.simulateSlapgridCP(remote_server)
      self.tic()
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
      connection_dict = owner_software_instance.getConnectionXmlAsDict()
      self.assertSameSet(('url_1', 'url_2'), connection_dict.keys())
      self.assertSameSet(
          ['http://%s/' % q.getIpAddress() for q in
              owner_software_instance.getAggregateValue().contentValues(portal_type='Internet Protocol Address')],
          connection_dict.values())

      self.checkRemoteInstanceAllocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference(),
          connection_dict_to_check=owner_software_instance.getConnectionXmlAsDict())

      # Destroy the instance, and ensure the remote one is destroyed too
      self.checkRemoteInstanceUnallocation(public_person.getUserId(),
          public_reference, public_instance_title,
          public_server_software, public_instance_type,
          remote_compute_node, project.getReference())

      self.login()

      # Report destruction from compute_node
      self.simulateSlapgridUR(remote_server)
      self.assertEqual(
        "",
        owner_software_instance.getAggregate("")
      )

    # Ensure no unexpected object has been created
    # 3 allocation supply/line/cell
    # 2 compute/remote node
    # 1 credential request
    # 1 instance tree
    # 6 open sale order / line
    # 3 assignment
    # 3 simulation movements
    # 3 sale packing list / line
    # 2 sale trade condition
    # 1 software installation
    # 1 software instance
    # 1 software product
    # 3 subscription requests
    self.assertRelatedObjectCount(remote_project, 'XXXX')

    # Ensure no unexpected object has been created
    # 3 allocation supply/line/cell
    # 1 compute node
    # 1 credential request
    # 1 instance tree
    # 4 open sale order / line
    # 3 assignment
    # 2 simulation movements
    # 2 sale packing list / line
    # 2 sale trade condition
    # 1 software instance
    # 1 software product
    # 2 subscription requests
    self.assertRelatedObjectCount(project, 'XXX')

    self.checkERP5StateBeforeExit()
