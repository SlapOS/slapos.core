# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.SlapOSTestCaseDefaultScenarioMixin import DefaultScenarioMixin
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime
from DateTime import DateTime


class TestSlapOSVirtualMasterScenarioMixin(DefaultScenarioMixin):

  def requestRemoteNode(self, project, remote_project, remote_person):
    remote_node = self.portal.compute_node_module.newContent(
      portal_type='Remote Node',
      title='remote-%s' % self.generateNewId(),
      follow_up_value=project,
      destination_project_value=remote_project.getRelativeUrl(),
      destination_section_value=remote_person.getRelativeUrl(),
      # XXX
      capacity_scope='close'
    )
    self.setServerOpenPublic(remote_node)
    remote_node.setCapacityScope('open')

    # XXX format
    partition = remote_node.newContent(
      portal_type='Compute Partition',
      reference='slapremote0'
    )
    partition.markFree()
    partition.validate()
    remote_node.validate()
    return remote_node

  def addSoftwareProduct(self, title, project, public_server_software,
                         public_instance_type):
    software_product = self.portal.software_product_module.newContent(
      portal_type="Software Product",
      title=title,
      follow_up_value=project,
    )
    software_product.newContent(
      portal_type="Software Product Release Variation",
      title="my old release",
      url_string=public_server_software + '-1'
    )
    release_variation = software_product.newContent(
      portal_type="Software Product Release Variation",
      title="my current release",
      url_string=public_server_software
    )
    software_product.newContent(
      portal_type="Software Product Release Variation",
      title="my futur release",
      url_string=public_server_software + '+1'
    )
    software_product.newContent(
      portal_type="Software Product Type Variation",
      title=public_instance_type + '-1'
    )
    type_variation = software_product.newContent(
      portal_type="Software Product Type Variation",
      title=public_instance_type
    )
    software_product.newContent(
      portal_type="Software Product Type Variation",
      title=public_instance_type + '+1'
    )
    software_product.validate()
    return software_product, release_variation, type_variation


  def stepcheckERP5Consistency(self):
    # Customer BT5 Configurator Item : no idea where the issue comes from
    not_consistent_document = self.portal.portal_catalog.getResultValue(
      consistency_error=1,
      portal_type=NegatedQuery(SimpleQuery(portal_type=[
        'Business Configuration',
        'Configuration Save',
        'Customer BT5 Configurator Item',
        'Web Site'
      ])),
      sort_on=[('modification_date', 'DESC')]
    )
    if not_consistent_document is not None:
      # XXX check disabled
      assert not_consistent_document.checkConsistency() == [], not_consistent_document.checkConsistency()[0]


  def addInstanceNode(self, title, software_instance):
    instance_node = self.portal.compute_node_module.newContent(
      portal_type='Instance Node',
      title=title,
      specialise_value=software_instance,
      follow_up_value=software_instance.getFollowUpValue()
    )
    instance_node.validate()
    return instance_node


  def bootstrapVirtualMasterTest(self, is_virtual_master_accountable=True):
    self.web_site = self.portal.web_site_module.slapos_master_panel
    # some preparation
    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
      ]
    )

    ################################################################
    # lets join as slapos accountant, which will manages currencies
    self.logout()
    accountant_reference = 'accountant-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, accountant_reference)
    self.login()
    accountant_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=accountant_reference).getParentValue()
    self.addAccountingManagerAssignment(accountant_person)

    self.tic()
    # hooray, now it is time to create accounting data
    self.login(accountant_person.getUserId())

    currency = self.portal.currency_module.newContent(
      portal_type="Currency",
      reference="test-currency-%s" % self.generateNewId(),
      short_title="tc%s" % self.generateNewId(),
      base_unit_quantity=0.01
    )
    currency.validate()

    ################################################################
    # lets join as slapos sales manager, which will manages trade condition
    self.logout()
    sale_reference = 'sales-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, sale_reference)
    self.login()
    sale_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=sale_reference).getParentValue()
    self.addSaleManagerAssignment(sale_person)

    self.tic()
    # hooray, now it is time to create sale data
    self.login(sale_person.getUserId())

    seller_organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation",
      title="test-seller-%s" % self.generateNewId(),
      # required to generate accounting report
      price_currency_value=currency
    )
    seller_bank_account = seller_organisation.newContent(
      portal_type="Bank Account",
      title="test_bank_account_%s" % self.generateNewId(),
      price_currency_value=currency
    )
    seller_bank_account.validate()
    seller_organisation.validate()

    # Sale Trade Condition for Tax
    sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference="Tax/payment for: %s" % currency.getRelativeUrl(),
      trade_condition_type="default",
      # XXX hardcoded
      specialise="business_process_module/slapos_ultimate_business_process",
      price_currency_value=currency,
      payment_condition_payment_mode='test-%s' % self.generateNewId()
    )
    sale_trade_condition.newContent(
      portal_type="Trade Model Line",
      reference="VAT",
      resource="service_module/slapos_tax",
      base_application="base_amount/invoicing/taxable",
      trade_phase="slapos/tax",
      price=0.2,
      quantity=1.0,
      membership_criterion_base_category=('price_currency', 'base_contribution'),
      membership_criterion_category=('price_currency/%s' % currency.getRelativeUrl(), 'base_contribution/base_amount/invoicing/taxable')
    )
    sale_trade_condition.validate()

    # Create Trade Condition to create Deposit
    self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference="For deposit",
      trade_condition_type="deposit",
      specialise_value=sale_trade_condition,
      source_value=seller_organisation,
      source_section_value=seller_organisation,
      price_currency_value=currency,
    ).validate()

    # Create Trade Condition to create Project
    if is_virtual_master_accountable:
      source_section_value = seller_organisation
      title = "Payable Virtual Master (%s)" % seller_organisation.getTitle()
    else:
      source_section_value = None
      title = "Free Virtual Master (%s)" % seller_organisation.getTitle()

    sale_trade_condition = self.portal.sale_trade_condition_module.newContent(
      portal_type="Sale Trade Condition",
      reference=title,
      trade_condition_type="virtual_master",
      specialise_value=sale_trade_condition,
      source_value=seller_organisation,
      source_section_value=source_section_value,
      price_currency_value=currency,
    )
    sale_trade_condition.validate()

    sale_supply = self.portal.sale_supply_module.newContent(
      portal_type="Sale Supply",
      price_currency_value=currency
    )
    # XXX Put price in sale supply module
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      base_price=42,
      resource="service_module/slapos_virtual_master_subscription"
    )
    sale_supply.validate()

    return currency, seller_organisation, seller_bank_account, sale_person

  def checkERP5StateBeforeExit(self):
    self.logout()
    self.stepCallAlarmList()
    self.tic()
    self.login()
    """
    self.stepcheckERP5Consistency()
    # after accept, an email is send containing the reset link
    last_message = self.portal.MailHost._last_message
    assert last_message is None, last_message
    """


  def assertRelatedObjectCount(self, document, count):
    related_object_list = document.Base_getRelatedObjectList(**{'category.category_strict_membership': 1})
    related_object_list = [x.getRelativeUrl() for x in related_object_list]
    related_object_list.sort()
    assert len(related_object_list) == count, '%i\n%s' % (len(related_object_list), '\n'.join(related_object_list))

  def createProductionManager(self, project):
    production_manager_reference = 'production_manager-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, production_manager_reference)

    self.login()
    production_manager_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=production_manager_reference).getParentValue()

    self.addProjectProductionManagerAssignment(production_manager_person, project)
    self.tic()
    return production_manager_person

  def bootstrapAccountingTest(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest()
    self.tic()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    owner_reference = 'project-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()
    self.tic()
    self.logout()

    self.login(sale_person.getUserId())
    with PinnedDateTime(self, DateTime('2020/01/01')):
      project_relative_url = self.addProject(
        is_accountable=True,
        person=owner_person,
        currency=currency
      )
      self.tic()
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
    return owner_person, currency, project


class TestSlapOSVirtualMasterScenario(TestSlapOSVirtualMasterScenarioMixin):

  def test_virtual_master_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.tic()

    self.logout()
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

    public_server_title = 'Public Server for %s' % owner_reference
    public_server_id = self.requestComputeNode(public_server_title, project.getReference())
    public_server = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=public_server_id)
    self.setAccessToMemcached(public_server)
    self.assertNotEqual(None, public_server)
    self.setServerOpenPublic(public_server)
    public_server.generateCertificate()

    # and install some software on them
    public_server_software = self.generateNewSoftwareReleaseUrl()
    public_instance_type = 'public type'

    self.supplySoftware(public_server, public_server_software)

    # format the compute_nodes
    self.formatComputeNode(public_server)

    software_product, release_variation, type_variation = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.addAllocationSupply("for compute node", public_server, software_product,
                             release_variation, type_variation)

    self.tic()
    self.logout()
    self.login()

    self.checkServiceSubscriptionRequest(public_server)

    # join as the another visitor and request software instance on public
    # compute_node
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        public_server, project.getReference())

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type='ERP5 Login', reference=public_reference).getParentValue()
    self.login(owner_person.getUserId())

    # and the instances
    self.checkInstanceUnallocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type, public_server,
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
    # Ensure no unexpected object has been created
    # 3 allocation supply, line, cell
    # 1 compute node
    # 1 credential request
    # 1 instance tree
    # 3 open sale order XXX * 2 why
    # 3 assignment
    # 3 simulation movement
    # 3 sale packing list / line
    # 2 sale trade condition ( a 3rd trade condition is not linked to the project)
    # 1 software installation
    # 1 software instance
    # 1 software product
    # 3 subscription request
    self.assertRelatedObjectCount(project, 29)

    self.checkERP5StateBeforeExit()


  def test_deposit_with_accounting_scenario(self):
    currency, _, _, _ = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=True)

    self.logout()
    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()
    self.tic()

    # hooray
    self.logout()
    self.login(owner_person.getUserId())

    # XXX XXX do reservation payment for a huge amount, to check if other services are ok
    total_price = 1234

    # Action to submit project subscription
    def wrapWithShadow(person, *arg):
      return person.Person_addDepositPayment(*arg)
    payment_transaction = owner_person.Person_restrictMethodAsShadowUser(
      shadow_document=owner_person,
      callable_object=wrapWithShadow,
      argument_list=[owner_person, total_price, currency.getRelativeUrl(), 1])
    self.tic()
    self.logout()
    self.login()
    payment_transaction.PaymentTransaction_acceptDepositPayment()
    self.tic()

    assert payment_transaction.receivable.getGroupingReference(None) is not None

    self.checkERP5StateBeforeExit()


  def test_virtual_master_with_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest()

    self.logout()
    # lets join as slapos administrator, which will manager the project
    owner_reference = 'project-%s' % self.generateNewId()
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

    project_relative_url = self.addProject(is_accountable=True, person=owner_person, currency=currency)

    self.logout()

    self.login()
    project = self.portal.restrictedTraverse(project_relative_url)

    payment_transaction = owner_person.Person_addDepositPayment(99*10, currency.getRelativeUrl(), 1)
    payment_transaction.PaymentTransaction_acceptDepositPayment()

    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % project.getRelativeUrl()
      ]
    )

    public_server_software = self.generateNewSoftwareReleaseUrl()
    public_instance_type = 'public type'

    software_product, release_variation, type_variation = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.logout()
    self.login(sale_person.getUserId())

    sale_supply = self.portal.sale_supply_module.newContent(
      portal_type="Sale Supply",
      title="price for %s" % project.getRelativeUrl(),
      source_project_value=project,
      price_currency_value=currency
    )
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      base_price=9,
      resource_value=software_product
    )
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      base_price=99,
      resource="service_module/slapos_compute_node_subscription"
    )
    sale_supply.validate()

    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()

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

    # join as the another visitor and request software instance on public
    # compute_node
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    payment_transaction = public_person.Person_addDepositPayment(99*10, currency.getRelativeUrl(), 1)
    payment_transaction.PaymentTransaction_acceptDepositPayment()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        public_server, project.getReference())

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type='ERP5 Login', reference=public_reference).getParentValue()
    self.login(owner_person.getUserId())

    # and the instances
    self.checkInstanceUnallocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type, public_server,
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

    # Check stock
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**{
      'group_by_section': False,
      'group_by_node': True,
      'group_by_variation': True,
      'resource_uid': software_product.getUid(),
      'node_uid': public_person.getUid(),
      'project_uid': None,
      'ledger_uid': self.portal.portal_categories.ledger.automated.getUid()
    })
    assert len(inventory_list) == 1, len(inventory_list)
    assert inventory_list[0].quantity == 1, inventory_list[0].quantity
    resource_vcl = [
      #'software_release/%s' % release_variation.getRelativeUrl(),
      'software_type/%s' % type_variation.getRelativeUrl()
    ]
    resource_vcl.sort()
    assert inventory_list[0].getVariationCategoryList() == resource_vcl, "%s %s" % (resource_vcl, inventory_list[0].getVariationCategoryList())

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(mirror_section_uid=public_person.getUid())
    assert len(transaction_list) == 2, len(transaction_list)
    assert transaction_list[0].total_price == 990.0, transaction_list[0].total_price
    assert transaction_list[1].total_price == -990.0, transaction_list[1].total_price

    self.login()

    # Ensure no unexpected object has been created
    # 3 accounting transaction / line
    # 3 allocation supply / line / cell
    # 1 compute node
    # 2 credential request
    # 1 instance tree
    # 6 open sale order / line
    # 5 (can reduce to 2) assignment
    # 16 simulation mvt
    # 3 packing list / line
    # 3 sale supply / line
    # 2 sale trade condition
    # 1 software installation
    # 1 software instance
    # 1 software product
    # 3 subscription requests
    self.assertRelatedObjectCount(project, 51)

    self.checkERP5StateBeforeExit()


  def test_virtual_master_slave_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.web_site = self.portal.web_site_module.slapos_master_panel

    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()
    self.tic()

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

    # and install some software on them
    public_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(public_server, public_server_software)

    #software_product, release_variation, type_variation = self.addSoftwareProduct(
    public_instance_type = 'public type'
    software_product, software_release, software_type = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.addAllocationSupply("for compute node", public_server, software_product,
                             software_release, software_type)

    # format the compute_nodes
    self.formatComputeNode(public_server)

    # join as the another visitor and request software instance on public
    # compute_node
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        public_server, project.getReference())

    # hooray, now it is time to create compute_nodes
    self.login(owner_person.getUserId())
    instance_node_title = 'Shared Instance for %s' % owner_reference
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

    slave_instance_title = 'Slave title %s' % self.generateNewId()
    self.checkSlaveInstanceAllocation(public_person.getUserId(),
        public_reference, slave_instance_title,
        slave_server_software, slave_instance_type,
        public_server, project.getReference())

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type='ERP5 Login', reference=public_reference).getParentValue()
    self.login(owner_person.getUserId())

    # and the instances
    self.checkSlaveInstanceUnallocation(public_person.getUserId(),
        public_reference, slave_instance_title,
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
    # Ensure no unexpected object has been created
    # 6 allocation supply/line/cell
    # 2 compute/instance node
    # 1 credential request
    # 2 instance tree
    # 9 open sale order / line
    # 3 assignment
    # 4 simulation movement
    # 4 sale packing list
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 2 software product
    # 4 subscription request
    self.assertRelatedObjectCount(project, 42)

    self.checkERP5StateBeforeExit()


  def test_virtual_master_slave_on_same_tree_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.web_site = self.portal.web_site_module.slapos_master_panel

    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    owner_reference = 'owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, owner_reference)

    self.login()
    owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=owner_reference).getParentValue()
    self.tic()

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

    # and install some software on them
    public_server_software = self.generateNewSoftwareReleaseUrl()
    self.supplySoftware(public_server, public_server_software)

    #software_product, release_variation, type_variation = self.addSoftwareProduct(
    public_instance_type = 'public type'
    software_product, software_release, software_type = self.addSoftwareProduct(
      "instance product", project, public_server_software, public_instance_type
    )

    self.addAllocationSupply("for compute node", public_server, software_product,
                             software_release, software_type,
                             is_slave_on_same_instance_tree_allocable=True)

    # format the compute_nodes
    self.formatComputeNode(public_server)

    # join as the another visitor and request software instance on public
    # compute_node
    self.logout()
    public_reference = 'public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.checkInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        public_server, project.getReference())

    self.tic()

    # request slave instance on the same instance tree
    self.login(public_person.getUserId())
    slave_instance_title = 'Slave title %s' % self.generateNewId()
    self.checkInstanceTreeSlaveInstanceAllocation(
      public_person.getUserId(),
      public_reference, public_instance_title,
      slave_instance_title,
      public_server_software, public_instance_type,
      public_server, project.getReference()
    )

    self.login()
    # Ensure no unexpected object has been created
    # 3 allocation supply/line/cell
    # 1 compute node
    # 1 credential request
    # 1 instance tree
    # 6 open sale order / line
    # 3 assignments
    # 3 simulation movements
    # 3 sale packing list / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 3 subscription request
    self.assertRelatedObjectCount(project, 30)

    self.checkERP5StateBeforeExit()


  def test_virtual_master_on_remote_tree_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.web_site = self.portal.web_site_module.slapos_master_panel

    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    remote_owner_reference = 'remote-owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, remote_owner_reference)

    self.login()
    remote_owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=remote_owner_reference).getParentValue()
    self.tic()

    self.logout()
    self.login(sale_person.getUserId())
    # create a default project
    remote_project_relative_url = self.addProject(person=remote_owner_person, currency=currency)

    self.logout()
    self.login()
    remote_project = self.portal.restrictedTraverse(remote_project_relative_url)

    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % remote_project.getRelativeUrl()
      ]
    )
    self.tic()

    # hooray, now it is time to create compute_nodes
    self.login(remote_owner_person.getUserId())

    remote_server_title = 'Remote Server for %s' % remote_owner_person
    remote_server_id = self.requestComputeNode(remote_server_title, remote_project.getReference())
    remote_server = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=remote_server_id)
    self.setAccessToMemcached(remote_server)
    self.assertNotEqual(None, remote_server)
    self.setServerOpenPublic(remote_server)
    remote_server.generateCertificate()

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
    self.logout()
    remote_public_reference = 'remote-public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, remote_public_reference)

    self.login()
    remote_public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=remote_public_reference).getParentValue()

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
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

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
    self.assertRelatedObjectCount(remote_project, 30)

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
    self.assertRelatedObjectCount(project, 23)

    self.checkERP5StateBeforeExit()


  def test_virtual_master_slave_instance_on_remote_tree_without_accounting_scenario(self):
    currency, _, _, sale_person = self.bootstrapVirtualMasterTest(is_virtual_master_accountable=False)

    self.web_site = self.portal.web_site_module.slapos_master_panel

    # some preparation
    self.logout()

    # lets join as slapos administrator, which will own few compute_nodes
    remote_owner_reference = 'remote-owner-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, remote_owner_reference)

    self.login()
    remote_owner_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=remote_owner_reference).getParentValue()
    self.tic()

    self.logout()
    self.login(sale_person.getUserId())
    # create a default project
    remote_project_relative_url = self.addProject(person=remote_owner_person, currency=currency)

    self.logout()
    self.login()
    remote_project = self.portal.restrictedTraverse(remote_project_relative_url)

    preference = self.portal.portal_preferences.slapos_default_system_preference
    preference.edit(
      preferred_subscription_assignment_category_list=[
        'function/customer',
        'role/client',
        'destination_project/%s' % remote_project.getRelativeUrl()
      ]
    )
    self.tic()

    # hooray, now it is time to create compute_nodes
    self.login(remote_owner_person.getUserId())

    remote_server_title = 'Remote Server for %s' % remote_owner_person
    remote_server_id = self.requestComputeNode(remote_server_title, remote_project.getReference())
    remote_server = self.portal.portal_catalog.getResultValue(
        portal_type='Compute Node', reference=remote_server_id)
    self.setAccessToMemcached(remote_server)
    self.assertNotEqual(None, remote_server)
    self.setServerOpenPublic(remote_server)
    remote_server.generateCertificate()

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
                             remote_release_variation, remote_type_variation,
                             destination_value=remote_owner_person)

    private_instance_title = 'Private title %s' % self.generateNewId()
    self.checkInstanceAllocation(remote_owner_person.getUserId(),
        remote_owner_reference, private_instance_title,
        remote_server_software, remote_instance_type,
        remote_server, remote_project.getReference())

    # Convert the Software Instance into an Instance Node
    # to explicitely mark it as accepting Slave Instance
    private_software_instance = self.portal.portal_catalog.getResultValue(
        portal_type='Software Instance', title=private_instance_title)
    instance_node_title = 'Shared Instance for %s' % remote_owner_reference
    instance_node = self.addInstanceNode(instance_node_title, private_software_instance)

    self.addAllocationSupply(
      "for instance node", instance_node, remote_software_product,
      remote_release_variation, remote_type_variation)

    # join as the another visitor and request software instance on public
    # compute_node
    self.logout()
    remote_public_reference = 'remote-public-%s' % self.generateNewId()
    self.joinSlapOS(self.web_site, remote_public_reference)

    self.login()
    remote_public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=remote_public_reference).getParentValue()

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
    self.joinSlapOS(self.web_site, public_reference)

    self.login()
    public_person = self.portal.portal_catalog.getResultValue(
      portal_type="ERP5 Login",
      reference=public_reference).getParentValue()

    public_instance_title = 'Public title %s' % self.generateNewId()
    self.checkRemoteInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        remote_compute_node, project.getReference(),
        slave=True)

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
    self.assertEqual('Slave Instance', owner_software_instance.getPortalType())
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
        ['http://%s/%s' % (q.getIpAddress(), owner_software_instance.getReference()) for q in
            owner_software_instance.getAggregateValue().contentValues(portal_type='Internet Protocol Address')],
        connection_dict.values())

    self.checkRemoteInstanceAllocation(public_person.getUserId(),
        public_reference, public_instance_title,
        public_server_software, public_instance_type,
        remote_compute_node, project.getReference(),
        connection_dict_to_check=owner_software_instance.getConnectionXmlAsDict(),
        slave=True)

    self.login()

    # Ensure no unexpected object has been created
    # 6 allocation supply/line/cell
    # 3 compute/remote/instance node
    # 1 credential request
    # 2 instance tree
    # 9 open sale order / line
    # 3 assignment
    # 4 simulation movements
    # 4 sale packing list / line
    # 2 sale trade condition
    # 1 software installation
    # 2 software instance
    # 1 software product
    # 4 subscription requests
    self.assertRelatedObjectCount(remote_project, 42)

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
    self.assertRelatedObjectCount(project, 23)

    self.checkERP5StateBeforeExit()

"""
  def test_open_order_with_service_scenario(self):

    # create a default project
    project = self.addProject(is_accountable=True)
    person = self.portal.person_module.newContent(
      portal_type="Person",
      default_email_coordinate_text='a@example.org',
    )
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    bank_account = organisation.newContent(
      portal_type="Bank Account"
    )

    sale_trade_condition = project.getSpecialiseValue()

    service = self.portal.restrictedTraverse('service_module/slapos_virtual_master_subscription')

    for _ in range(1):
      hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type="Hosting Subscription",
        # XXX hardcoded
        ledger="automated",
        follow_up_value=project,
      )
      hosting_subscription.validate()
      start_date = hosting_subscription.HostingSubscription_calculateSubscriptionStartDate()

      # create open order
      open_sale_order = self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
        ledger=hosting_subscription.getLedger(),
        destination_project_value=project,
        source_value=organisation,
        source_section_value=organisation,
        source_payment_value=bank_account,
        destination_value=person,
        destination_section_value=person,
        destination_decision_value=person,
        price_currency_value=sale_trade_condition.getPriceCurrencyValue(),
        payment_mode="payzen",
        start_date=start_date,
        # Ensure stop date value is higher than start date
        # it will be updated by OpenSaleOrder_updatePeriod
        stop_date=start_date + 1,
        specialise_value=sale_trade_condition
      )

      open_sale_order.newContent(
        portal_type="Open Sale Order Line",
        quantity=10,
        price=2,
        resource_value=service,
        aggregate_value=[
          hosting_subscription,
          project
        ]
      )
      open_sale_order.order()
      open_sale_order.validate()
    self.tic()

    # XXX Do this for every scenario tests
    self.logout()
    for _ in range(20):
      self.stepCallAlarmList()
      self.tic()
    self.login()

    # Check stock
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**{
      'group_by_section': False,
      'group_by_node': True,
      'group_by_variation': True,
      'resource_uid': service.getUid(),
      'node_uid': person.getUid(),
      'project_uid': project.getUid(),
      'ledger_uid': hosting_subscription.getLedgerUid()
    })
    assert len(inventory_list) == 1, len(inventory_list)
    assert inventory_list[0].quantity == 10, inventory_list[0].quantity
    assert inventory_list[0].getVariationCategoryList() == [], inventory_list[0].getVariationCategoryList()

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(mirror_section_uid=person.getUid())
    assert len(transaction_list) == 1, len(transaction_list)
    assert transaction_list[0].total_price == 24, transaction_list[0].total_price

    # Ensure no unexpected object has been created
    # destination project:
    # 1 open order
    # 1 hosting subscription
    # 2 accounting transaction
    # 1 packing list
    # 7 simulation mvt
    # aggregate:
    # 1 invoice line
    # 1 packing list line
    # 1 open order line

    related_object_list = project.Base_getRelatedObjectList(**{'category.category_strict_membership': 1})
    assert len(related_object_list) == 15, [x.getRelativeUrl() for x in related_object_list]

    self.stepcheckERP5Consistency()

    # after accept, an email is send containing the reset link
    last_message = self.portal.MailHost._last_message
    assert last_message is None, last_message


  def test_open_order_with_software_product_scenario(self):
    # create a default project
    project = self.addProject(is_accountable=True)
    person = self.portal.person_module.newContent(
      portal_type="Person",
      default_email_coordinate_text='a@example.org',
    )
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    bank_account = organisation.newContent(
      portal_type="Bank Account"
    )

    sale_trade_condition = project.getSpecialiseValue()

    software_product = self.portal.software_product_module.newContent(
      portal_type="Software Product",
      title="foo software product",
      follow_up_value=project,
    )
    software_product.newContent(
      portal_type="Software Product Release Variation",
      title="my super release"
    )
    software_product.newContent(
      portal_type="Software Product Type Variation",
      title="my super type"
    )
    software_product.validate()

    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type="Instance Tree",
      follow_up_value=project
    )

    for _ in range(1):
      hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type="Hosting Subscription",
        # XXX hardcoded
        ledger="automated",
      )
      hosting_subscription.validate()
      start_date = hosting_subscription.HostingSubscription_calculateSubscriptionStartDate()

      # create open order
      open_sale_order = self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
        ledger=hosting_subscription.getLedger(),
        destination_project_value=project,
        source_value=organisation,
        source_section_value=organisation,
        source_payment_value=bank_account,
        destination_value=person,
        destination_section_value=person,
        destination_decision_value=person,
        price_currency_value=sale_trade_condition.getPriceCurrencyValue(),
        payment_mode="payzen",
        start_date=start_date,
        # Ensure stop date value is higher than start date
        # it will be updated by OpenSaleOrder_updatePeriod
        stop_date=start_date + 1,
        specialise_value=sale_trade_condition
      )

      resource_vcl = list(software_product.getVariationCategoryList(
                                     omit_individual_variation=0))
      resource_vcl.sort()
      open_order_line = open_sale_order.newContent(
        portal_type="Open Sale Order Line",
        resource_value=software_product,
        variation_category_list=resource_vcl
      )


      base_id = 'path'
      cell_key = list(open_order_line.getCellKeyList(base_id=base_id))[0]
      #cell_key_list.sort()
      open_order_cell = open_order_line.newCell(
        base_id=base_id,
        portal_type='Open Sale Order Cell',
        *cell_key
      )
      open_order_cell.edit(
        mapped_value_property_list=['price','quantity'],
        price=3,
        quantity=4,
        predicate_category_list=cell_key,
        variation_category_list=cell_key,
        aggregate_value=[
          hosting_subscription,
          instance_tree
        ],
      )

      open_sale_order.order()
      open_sale_order.validate()
    self.tic()

    # XXX Do this for every scenario tests
    self.logout()
    for _ in range(20):
      self.stepCallAlarmList()
      self.tic()
    self.login()

    # Check stock
    inventory_list = self.portal.portal_simulation.getCurrentInventoryList(**{
      'group_by_section': False,
      'group_by_node': True,
      'group_by_variation': True,
      'resource_uid': software_product.getUid(),
      'node_uid': person.getUid(),
      'project_uid': None,
      'ledger_uid': hosting_subscription.getLedgerUid()
    })
    assert len(inventory_list) == 1, len(inventory_list)
    assert inventory_list[0].quantity == 4, inventory_list[0].quantity
    assert inventory_list[0].getVariationCategoryList() == resource_vcl, inventory_list[0].getVariationCategoryList()

    # Check accounting
    transaction_list = self.portal.account_module.receivable.Account_getAccountingTransactionList(mirror_section_uid=person.getUid())
    assert len(transaction_list) == 1, len(transaction_list)
    assert transaction_list[0].total_price == 14.4, transaction_list[0].total_price

    # Ensure no unexpected object has been created
    # destination project:
    # 1 open order
    # 2 accounting transaction
    # 1 packing list
    # 7 simulation mvt
    # 1 instance tree
    # 1 software product
    # acquisition...
    # 1 open order line
    # 1 open order cell

    related_object_list = project.Base_getRelatedObjectList(**{'category.category_strict_membership': 1})
    assert len(related_object_list) == 15, [x.getRelativeUrl() for x in related_object_list]

    self.stepcheckERP5Consistency()

    # after accept, an email is send containing the reset link
    last_message = self.portal.MailHost._last_message
    assert last_message is None, last_message
"""