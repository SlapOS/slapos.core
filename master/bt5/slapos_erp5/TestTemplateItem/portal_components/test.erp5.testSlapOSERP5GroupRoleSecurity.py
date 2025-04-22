# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2012-2019  Nexedi SA and Contributors.
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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixinWithAbort
from AccessControl import getSecurityManager
import transaction

class TestSlapOSGroupRoleSecurityCoverage(SlapOSTestCaseMixinWithAbort):
  maxDiff = None

  def testCoverage(self):
    """ Test which Portal types are not covered by this test.
    """

    test_source_code = ""
    for test_file_id in self.security_group_role_test_id_list:
      test_source_code += self.portal.portal_components[test_file_id].getTextContent()

    test_list = []
    for pt in self.portal.portal_types.objectValues():
      if 0 < len(pt.contentValues(portal_type="Role Information")):
        test_klass = "class Test%s(" % "".join(pt.getId().split(" "))
        if test_klass not in test_source_code:
          test_list.append(pt.getId())
    test_list.sort()
    self.assertEqual(test_list, [])

  def testLocalRoleGroup(self):
    """
    Check that all role definitions use a local role group
    XXX how to check the consistency
    """
    test_list = []
    expected_failure_dict = {
      # comes from generic erp5 bt5. Unused
      'Query - Acquired Assignee': None,
      # Like 'user' group, but for instance
      # there is no local_role_group for single instance user
      'Slave Instance - Software Instance which provides this Slave Instance': None
    }
    for pt in self.portal.portal_types.objectValues():
      for role_information in pt.contentValues(portal_type="Role Information"):
        group = role_information.getLocalRoleGroupValue()
        role_title = '%s - %s' % (pt.getId(), role_information.getTitle())
        if ((group is None) and (role_title not in expected_failure_dict)) or \
           ((group is not None) and (role_title in expected_failure_dict)):
          test_list.append(role_title)
    test_list.sort()
    self.assertEqual(test_list, [])

class TestSlapOSGroupRoleSecurityMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.user_id = getSecurityManager().getUser().getId()

  def _getLocalRoles(self, context):
    return [x[0] for x in context.get_local_roles()]

  def _permissionsOfRole(self, context, role):
    return [x['name'] for x in context.permissionsOfRole(role) \
          if x['selected'] == 'SELECTED']

  def _acquirePermissions(self, context):
    return [x['name'] for x in context.permission_settings() \
          if x['acquire'] == 'CHECKED']

  def assertPermissionsOfRole(self, context, role, permission_list):
    self.assertSameSet(
      permission_list,
      self._permissionsOfRole(context, role))

  def assertAcquiredPermissions(self, context, permission_list):
    self.assertSameSet(
      permission_list,
      self._acquirePermissions(context))

  def assertSecurityGroup(self, context, security_group_list, acquired):
    self.assertEqual(acquired, context._getAcquireLocalRoles())
    self.assertSameSet(
      security_group_list,
      self._getLocalRoles(context)
    )

  def assertRoles(self, context, security_group, role_list):
    self.assertSameSet(
      role_list,
      context.get_local_roles_for_userid(security_group)
    )


class TestAccountModule(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountModule(self):
    module = self.portal.account_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', module.Base_getOwnerId(), 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestAccount(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingFunction(self):
    product = self.portal.account_module.newContent(
        portal_type='Account')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestAccountingPeriod(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingFunction(self):
    product = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(
        portal_type='Accounting Period')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestAccountingTransactionModule(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingTransactionModule(self):
    module = self.portal.accounting_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', 'F-PRODUCTION*', module.Base_getOwnerId(),
         'R-SHADOW-PERSON', 'F-CUSTOMER'], True)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Author'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestPaymentTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_PaymentTransaction_AccountingFunction_LedgerNotAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_PaymentTransaction_AccountingFunction_LedgerAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(ledger='automated')
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_PaymentTransaction_UserWithoutLedger(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(
        destination_value=person,
        )
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_PaymentTransaction_UserLedger(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(
        destination_section_value=person,
        ledger='automated'
        )
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id, person.getUserId(),
         shadow_user_id], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, shadow_user_id, ['Assignee'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_PaymentTransaction_OrganisationLedger(self):
    organisation = self.portal.organisation_module.newContent(
      portal_type='Organisation',
      title='TESTORGA-%s' % self.generateNewId()
    )
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(
        destination_section_value=organisation,
        ledger='automated'
        )
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', 'R-SHADOW-PERSON', self.user_id ], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestSaleInvoiceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_SaleInvoiceTransaction_AccountingFunction_LedgerNotAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction', created_by_builder=1)
    self.assertEqual(product.getLedger(), None)
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_SaleInvoiceTransaction_AccountingFunction_LedgerAutomated(self):
    """No user, no shadow"""
    product = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    product.edit(ledger='automated')
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id ], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_SaleInvoiceTransaction_User(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    product.edit(
        ledger='automated',
        destination_value=person,
        )
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id, person.getUserId(),
         'SHADOW-%s' % person.getUserId()], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, 'SHADOW-%s' % person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestAccountingTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingTransaction_LedgerNotAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Accounting Transaction')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_AccountingTransaction_LedgerAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Accounting Transaction')
    product.edit(ledger='automated')
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestBalanceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingFunction_LedgerNotAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Balance Transaction')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_AccountingFunction_LedgerAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Balance Transaction')
    product.edit(ledger='automated')
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestPurchaseInvoiceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_AccountingFunction_LedgerNotAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Purchase Invoice Transaction')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', self.user_id], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_AccountingFunction_LedgerAutomated(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Purchase Invoice Transaction')
    product.edit(ledger='automated')
    self.assertSecurityGroup(product,
        ['F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestAllocationSupplyModule(TestSlapOSGroupRoleSecurityMixin):
  def test_AllocationSupplyModule(self):
    module = self.portal.allocation_supply_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestAllocationSupply(TestSlapOSGroupRoleSecurityMixin):
  def test_AllocationSupply_default(self):
    supply = self.portal.allocation_supply_module.newContent(
        portal_type='Allocation Supply')
    self.assertSecurityGroup(supply,
        [self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])

  def test_AllocationSupply_DestinationCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)

    supply = self.portal.allocation_supply_module.newContent(
        portal_type='Allocation Supply')
    supply.edit(
        destination_value=person,
        )
    self.assertSecurityGroup(supply,
        [self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])

    supply.validate()
    self.assertSecurityGroup(supply,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(supply, person.getUserId(), ['Auditor'])
    self.assertRoles(supply, self.user_id, ['Owner'])

    supply.invalidate()
    self.assertSecurityGroup(supply,
        [self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])

  def test_AllocationSupply_DestinationProject(self):
    project = self.addProject()
    supply = self.portal.allocation_supply_module.newContent(
        portal_type='Allocation Supply')
    supply.edit(
        destination_project_value=project,
        )

    self.assertSecurityGroup(supply, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(supply, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

    supply.validate()
    self.assertSecurityGroup(supply, [self.user_id,
        '%s_F-CUSTOMER' % project.getReference(),
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])
    self.assertRoles(supply, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(supply, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

    supply.invalidate()
    self.assertSecurityGroup(supply, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(supply, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

class TestAssignment(TestSlapOSGroupRoleSecurityMixin):
  def test_Assignment_Sale_Accountant(self):
    assignment = self.portal.person_module.newContent(
        portal_type='Person').newContent(portal_type='Assignment')
    self.assertSecurityGroup(assignment,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN', 'F-ACCMAN', 'F-ACCAGT'], False)
    self.assertRoles(assignment, 'F-ACCMAN', ['Auditor'])
    self.assertRoles(assignment, 'F-ACCAGT', ['Auditor'])
    self.assertRoles(assignment, self.user_id, ['Owner'])
    self.assertRoles(assignment, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(assignment, 'F-SALEAGT', ['Assignee'])

class TestComputeNodeModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ComputeNodeModule(self):
    module = self.portal.compute_node_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'R-COMPUTER', 'F-CUSTOMER', 'R-INSTANCE', module.Base_getOwnerId()],
        False)
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestComputeNode(TestSlapOSGroupRoleSecurityMixin):
  def test_ComputeNode_userId(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    self.assertSecurityGroup(compute_node,
        [self.user_id, compute_node.getUserId(), 'F-SALE*'], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(compute_node, 'F-SALE*', ['Auditor'])

    compute_node.edit(user_id=None)
    self.assertSecurityGroup(compute_node,
        [self.user_id, 'F-SALE*'], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, 'F-SALE*', ['Auditor'])

  def test_ComputeNode_ProjectMember(self):
    project = self.addProject()
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node')
    compute_node.edit(
        follow_up_value=project)

    self.assertSecurityGroup(compute_node, [
      self.user_id,
      compute_node.getUserId(),
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
      '%s_F-CUSTOMER' % project.getReference(),
      '%s_R-INSTANCE' % project.getReference(),
      'F-SALE*',
    ], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(compute_node, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(compute_node, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(compute_node, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])
    self.assertRoles(compute_node, '%s_R-INSTANCE' % project.getReference(), ['Auditor'])
    self.assertRoles(compute_node, 'F-SALE*', ['Auditor'])


class TestInstanceNode(TestSlapOSGroupRoleSecurityMixin):
  def test_InstanceNode_userId(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Instance Node')
    self.assertSecurityGroup(compute_node,
        [self.user_id], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])

    compute_node.edit(user_id=None)
    self.assertSecurityGroup(compute_node,
        [self.user_id], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])

  def test_InstanceNode_ProjectMember(self):
    project = self.addProject()
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Instance Node')
    compute_node.edit(
        follow_up_value=project)

    self.assertSecurityGroup(compute_node, [
      self.user_id,
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
      '%s_F-CUSTOMER' % project.getReference(),
    ], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(compute_node, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(compute_node, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])


class TestRemoteNode(TestSlapOSGroupRoleSecurityMixin):
  def test_RemoteNode_userId(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Remote Node')
    self.assertSecurityGroup(compute_node,
        [self.user_id], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])

    compute_node.edit(user_id=None)
    self.assertSecurityGroup(compute_node,
        [self.user_id], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])

  def test_RemoteNode_ProjectMember(self):
    project = self.addProject()
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Remote Node')
    compute_node.edit(
        follow_up_value=project)

    self.assertSecurityGroup(compute_node, [
      self.user_id,
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
      '%s_F-CUSTOMER' % project.getReference(),
      '%s_R-INSTANCE' % project.getReference(),
    ], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(compute_node, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(compute_node, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])
    self.assertRoles(compute_node, '%s_R-INSTANCE' % project.getReference(), ['Auditor'])


class TestComputerModelModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ComputerModelModule(self):
    module = self.portal.computer_model_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', 'R-SHADOW-PERSON', module.Base_getOwnerId()],
        False)
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestComputerModel(TestSlapOSGroupRoleSecurityMixin):
  document_portal_type = 'Computer Model'
  def test_ComputerModel_default(self):
    model = self.portal.getDefaultModuleValue(self.document_portal_type).newContent(
        portal_type=self.document_portal_type)
    self.assertSecurityGroup(model,
        ['R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(model, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(model, self.user_id, ['Owner'])

  def test_ComputerModel_ProjectMember(self):
    project = self.addProject()
    compute_node = self.portal.getDefaultModuleValue(self.document_portal_type).newContent(
        portal_type=self.document_portal_type)
    compute_node.edit(
        follow_up_value=project)

    self.assertSecurityGroup(compute_node, [
      self.user_id,
      'R-SHADOW-PERSON',
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
      '%s_F-CUSTOMER' % project.getReference(),
    ], False)
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(compute_node, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(compute_node, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(compute_node, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])


class TestComputerNetworkModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ComputerNetworkModule(self):
    module = self.portal.computer_network_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', 'R-SHADOW-PERSON', module.Base_getOwnerId()],
        False)
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestComputerNetwork(TestComputerModel):
  document_portal_type = 'Computer Network'



class TestCurrencyModule(TestSlapOSGroupRoleSecurityMixin):
  def test_CurrencyModule(self):
    module = self.portal.currency_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', 'F-PRODUCTION*', module.Base_getOwnerId(),
         'R-SHADOW-PERSON', 'F-CUSTOMER', 'F-SALE*'], True)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestCurrency(TestSlapOSGroupRoleSecurityMixin):
  def test_Currency(self):
    product = self.portal.currency_module.newContent(
        portal_type='Currency')
    self.assertSecurityGroup(product,
        ['F-ACCMAN', 'F-ACCAGT', 'F-PRODUCTION*', self.user_id,
         'R-SHADOW-PERSON', 'F-CUSTOMER', 'F-SALE*'], False)
    self.assertRoles(product, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(product, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(product, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(product, 'F-SALE*', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])


class TestEventModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.event_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-SALE*', 'F-CUSTOMER', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestMailMessage(TestSlapOSGroupRoleSecurityMixin):
  event_portal_type = 'Mail Message'
  def test_default(self):
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    self.assertSecurityGroup(product,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(product, 'F-SALEAGT', ['Assignee'])

  def test_SourceCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    product.edit(
        source_value=person,
        )
    self.assertSecurityGroup(product,
        [person.getUserId(), self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(product, 'F-SALEAGT', ['Assignee'])

  def test_DestinationCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    product.edit(
        destination_value=person,
        )
    self.assertSecurityGroup(product,
        [person.getUserId(), self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(product, 'F-SALEAGT', ['Assignee'])

  def test_SourceProject(self):
    project = self.addProject()
    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    event.edit(
        source_project_value=project
        )

    self.assertSecurityGroup(event, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(event, self.user_id, ['Owner'])
    self.assertRoles(event, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(event, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

  def test_DestinationProject(self):
    project = self.addProject()
    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    event.edit(
        destination_project_value=project
        )

    self.assertSecurityGroup(event, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(event, self.user_id, ['Owner'])
    self.assertRoles(event, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(event, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])


class TestShortMessage(TestMailMessage):
  event_portal_type = 'Short Message'

class TestSiteMessage(TestMailMessage):
  event_portal_type = 'Site Message'

class TestWebMessage(TestMailMessage):
  event_portal_type = 'Web Message'

class TestNote(TestMailMessage):
  event_portal_type = 'Note'

class TestPhoneCall(TestMailMessage):
  event_portal_type = 'Phone Call'

class TestVisit(TestMailMessage):
  event_portal_type = 'Visit'

class TestFaxMessage(TestMailMessage):
  event_portal_type = 'Fax Message'

class TestLetter(TestMailMessage):
  event_portal_type = 'Letter'

class TestAcknowledgement(TestMailMessage):
  event_portal_type = 'Acknowledgement'


class TestInstanceTreeModule(TestSlapOSGroupRoleSecurityMixin):
  def test_InstanceTreeModule(self):
    module = self.portal.instance_tree_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'R-COMPUTER', 'F-CUSTOMER', 'F-SALE*', 'R-INSTANCE', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestInstanceTree(TestSlapOSGroupRoleSecurityMixin):
  def test_InstanceTree_RelatedSoftwareInstanceGroup(self):
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree')
    subscription.edit(reference=reference)

    self.assertSecurityGroup(subscription, [self.user_id, 'F-SALE*', reference], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'F-SALE*', ['Auditor'])

  def test_InstanceTree_CustomOfTheInstanceTree(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference)
    subscription.edit(
        destination_section_value=customer)

    self.assertSecurityGroup(subscription, [self.user_id, 'F-SALE*', reference,
        customer.getUserId()], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, 'F-SALE*', ['Auditor'])
    self.assertRoles(subscription, customer.getUserId(), ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])

  def test_InstanceTree_ProjectMember(self):
    project = self.addProject()
    reference = 'TESTHS-%s' % self.generateNewId()
    project = self.portal.project_module.newContent(
        portal_type='Project')
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference)
    subscription.edit(
        follow_up_value=project)
    self.assertSecurityGroup(subscription, [self.user_id, 'F-SALE*', reference,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'F-SALE*', ['Auditor'])
    self.assertRoles(subscription, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(subscription, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])


class TestSoftwareInstallationModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareInstallationModule(self):
    module = self.portal.software_installation_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', 'R-COMPUTER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSoftwareInstallation(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareInstallation_default(self):
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')

    self.assertSecurityGroup(installation, [self.user_id], False)
    self.assertRoles(installation, self.user_id, ['Owner'])

  def test_SoftwareInstallation_ComputeNode(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    compute_node.edit(reference=compute_node_reference)

    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    installation.edit(
        aggregate_value=compute_node)

    self.assertSecurityGroup(installation, [self.user_id,
        compute_node.getUserId()], False)
    self.assertRoles(installation, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(installation, self.user_id, ['Owner'])

  def test_SoftwareInstallation_ProjectMember(self):
    project = self.addProject()
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    installation.edit(
        follow_up_value=project)

    self.assertSecurityGroup(installation, [
      self.user_id,
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
      '%s_F-CUSTOMER' % project.getReference(),
    ], False)
    self.assertRoles(installation, self.user_id, ['Owner'])
    self.assertRoles(installation, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(installation, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(installation, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])


class TestSoftwareInstanceModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareInstanceModule(self):
    module = self.portal.software_instance_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'R-COMPUTER', 'R-INSTANCE', 'F-CUSTOMER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSoftwareInstance(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareInstance_default(self):
    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')

    self.assertSecurityGroup(instance, [self.user_id], False)
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_SoftwareInstance_CustomerOfTheInstance(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)

    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')
    instance.edit(specialise=subscription.getRelativeUrl())

    self.assertSecurityGroup(instance, [customer.getUserId(),
        subscription_reference, self.user_id], False)
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_SoftwareInstance_ProjectMember(self):
    project = self.addProject()

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance')
    instance.edit(
      follow_up_value=project
    )

    self.assertSecurityGroup(instance, [
      self.user_id,
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference(),
    ], False)
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(instance, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])

  def test_SoftwareInstance_ComputeNode(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    compute_node.edit(reference=compute_node_reference)
    partition = compute_node.newContent(portal_type='Compute Partition')

    self.commit()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')
    instance.edit(aggregate_value=partition)

    self.assertSecurityGroup(instance, [compute_node.getUserId(),
        self.user_id], False)
    self.assertRoles(instance, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])


class TestSlaveInstance(TestSlapOSGroupRoleSecurityMixin):
  def test_SlaveInstance_default(self):
    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')

    self.assertSecurityGroup(instance, [self.user_id], False)
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_SlaveInstance_CustomerOfTheInstance(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)

    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    instance.edit(specialise=subscription.getRelativeUrl())

    self.assertSecurityGroup(instance, [customer.getUserId(),
        subscription_reference, self.user_id], False)
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_SlaveInstance_ProjectMember(self):
    project = self.addProject()
    instance = self.portal.software_instance_module.newContent(
      portal_type='Slave Instance')
    instance.edit(
      follow_up_value=project
    )

    self.assertSecurityGroup(instance, [
      self.user_id,
      '%s_F-PRODAGNT' % project.getReference(),
      '%s_F-PRODMAN' % project.getReference()
    ], False)
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(instance, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])

  def test_SlaveInstance_SoftwareInstanceWhichProvidesThisSlaveInstance(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module\
        .newContent(portal_type="Compute Node")
    compute_node.edit(reference=compute_node_reference)
    partition = compute_node.newContent(portal_type='Compute Partition')

    provider_reference = 'TESTSI-%s' % self.generateNewId()

    provider = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")

    provider.edit(reference=provider_reference,
        aggregate=partition.getRelativeUrl())
    provider.validate()

    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    instance.edit(aggregate=partition.getRelativeUrl())
    self.assertSecurityGroup(instance, [provider.getUserId(),
        compute_node.getUserId(), self.user_id], False)
    self.assertRoles(instance, provider.getUserId(), ['Assignor'])
    self.assertRoles(instance, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])


class TestSoftwareProductModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareProductModule(self):
    module = self.portal.software_product_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', 'F-SALE*', 'F-PRODUCTION*', 'F-CUSTOMER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSoftwareProduct(TestSlapOSGroupRoleSecurityMixin):
  def test_SoftwareProduct_default(self):
    product = self.portal.software_product_module.newContent(
        portal_type='Software Product')
    self.assertSecurityGroup(product,
        [self.user_id, 'F-ACCOUNTING*', 'F-SALE*'], False)
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, 'F-SALE*', ['Auditor'])

  def test_SoftwareProduct_Project(self):
    project = self.addProject()
    product = self.portal.software_product_module.newContent(
        portal_type='Software Product')
    product.edit(
        follow_up_value=project)
    self.assertSecurityGroup(product, [self.user_id,
        'F-ACCOUNTING*',
        'F-SALE*',
        '%s_F-CUSTOMER' % project.getReference(),
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(product, 'F-SALE*', ['Auditor'])
    self.assertRoles(product, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(product, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])
    self.assertRoles(product, '%s_F-CUSTOMER' % project.getReference(), ['Auditor'])


class TestSupportRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SupportRequestModule(self):
    module = self.portal.support_request_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-SALE*', 'F-CUSTOMER', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSupportRequest(TestSlapOSGroupRoleSecurityMixin):
  ticket_portal_type = 'Support Request'

  def test_SupportRequest_default(self):
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    self.assertSecurityGroup(support_request,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(support_request, 'F-SALEAGT', ['Assignee'])

  def test_SupportRequest_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        destination_decision_value=person,
        )
    self.assertSecurityGroup(support_request,
        [person.getUserId(), self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(support_request, 'F-SALEAGT', ['Assignee'])

  def test_SupportRequest_SourceProject(self):
    project = self.addProject()
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        source_project_value=project)
    self.assertSecurityGroup(support_request, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(support_request, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

  def test_SupportRequest_DestinationProject(self):
    project = self.addProject()
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        destination_project_value=project)
    self.assertSecurityGroup(support_request, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(support_request, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])


class TestRegularisationRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test_RegularisationRequestModule(self):
    module = self.portal.regularisation_request_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-CUSTOMER', 'F-ACCOUNTING*', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])

class TestRegularisationRequest(TestSlapOSGroupRoleSecurityMixin):
  ticket_portal_type = 'Regularisation Request'

  def test_RegularisationRequest_default(self):
    ticket = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    self.assertSecurityGroup(ticket,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN', 'F-ACCMAN', 'F-ACCAGT'], False)
    self.assertRoles(ticket, self.user_id, ['Owner'])
    self.assertRoles(ticket, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(ticket, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-ACCAGT', ['Assignee'])

  def test_RegularisationRequest_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    ticket = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    ticket.edit(
        destination_decision_value=person,
        )
    self.assertSecurityGroup(ticket,
        [person.getUserId(), self.user_id, 'F-SALEAGT',
         'F-SALEMAN', 'F-ACCMAN', 'F-ACCAGT'], False)
    self.assertRoles(ticket, person.getUserId(), ['Auditor'])
    self.assertRoles(ticket, self.user_id, ['Owner'])
    self.assertRoles(ticket, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(ticket, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-ACCAGT', ['Assignee'])

  def test_RegularisationRequest_organisation(self):
    reference = 'TESTORG-%s' % self.generateNewId()
    org = self.portal.organisation_module.newContent(
      portal_type='Organisation',
      reference=reference)
    ticket = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    ticket.edit(
        destination_decision_value=org,
        )
    self.assertSecurityGroup(ticket,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN', 'F-ACCMAN', 'F-ACCAGT'], False)
    self.assertRoles(ticket, self.user_id, ['Owner'])
    self.assertRoles(ticket, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(ticket, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(ticket, 'F-ACCAGT', ['Assignee'])

class TestSystemEventModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SystemEventModule(self):
    module = self.portal.system_event_module
    self.assertSecurityGroup(module,
        ['R-SHADOW-PERSON', 'F-ACCOUNTING*', module.Base_getOwnerId(), 'F-IS*'], False)
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Author'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Author'])
    self.assertRoles(module, 'F-IS*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])

class TestPayzenEvent(TestSlapOSGroupRoleSecurityMixin):
  def test_PayzenEvent_default(self):
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    self.assertSecurityGroup(event,
        ['F-IS*', self.user_id], False)
    self.assertRoles(event, 'F-IS*', ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_PayzenEvent_ShadowUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    event.edit(
        destination_section_value=person,
        )
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(event,
        ['F-IS*', self.user_id, shadow_user_id], False)
    self.assertRoles(event, 'F-IS*', ['Auditor'])
    self.assertRoles(event, shadow_user_id, ['Assignee'])
    self.assertRoles(event, self.user_id, ['Owner'])

class TestWechatEvent(TestSlapOSGroupRoleSecurityMixin):
  def test_WechatEvent_default(self):
    event = self.portal.system_event_module.newContent(
        portal_type='Wechat Event')
    self.assertSecurityGroup(event,
        ['F-IS*', self.user_id], False)
    self.assertRoles(event, 'F-IS*', ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_WechatEvent_ShadowUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    event = self.portal.system_event_module.newContent(
        portal_type='Wechat Event')
    event.edit(
        destination_section_value=person,
        )
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(event,
        ['F-IS*', self.user_id, shadow_user_id], False)
    self.assertRoles(event, 'F-IS*', ['Auditor'])
    self.assertRoles(event, shadow_user_id, ['Assignee'])
    self.assertRoles(event, self.user_id, ['Owner'])


class TestUpgradeDecisionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.upgrade_decision_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])

class TestUpgradeDecision(TestSlapOSGroupRoleSecurityMixin):
  ticket_portal_type = 'Upgrade Decision'

  def test_UpgradeDecision_default(self):
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    self.assertSecurityGroup(support_request,
        [self.user_id], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])

  def test_UpgradeDecision_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        destination_decision_value=person,
        )
    self.assertSecurityGroup(support_request,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])

  def test_UpgradeDecision_SourceProject(self):
    project = self.addProject()
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        source_project_value=project)
    self.assertSecurityGroup(support_request, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(support_request, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

  def test_UpgradeDecision_DestinationProject(self):
    project = self.addProject()
    support_request = self.portal.getDefaultModuleValue(self.ticket_portal_type).newContent(
        portal_type=self.ticket_portal_type)
    support_request.edit(
        destination_project_value=project)
    self.assertSecurityGroup(support_request, [self.user_id,
        '%s_F-PRODAGNT' % project.getReference(),
        '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(support_request, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])


class TestWebPageModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.web_page_module
    self.assertSecurityGroup(module,
        ['F-MARKETING*', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-MARKETING*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])

class TestWebPage(TestSlapOSGroupRoleSecurityMixin):
  def test_MarketingFunction(self):
    document = self.portal.web_page_module.newContent(
        portal_type='Web Page')
    self.assertSecurityGroup(document,
        ['F-MARKETING*', self.user_id], False)
    self.assertRoles(document, 'F-MARKETING*', ['Assignor'])
    self.assertRoles(document, self.user_id, ['Owner'])

class TestWebTable(TestSlapOSGroupRoleSecurityMixin):
  def test_MarketingFunction(self):
    document = self.portal.web_page_module.newContent(
        portal_type='Web Table')
    self.assertSecurityGroup(document,
        ['F-MARKETING*', self.user_id], False)
    self.assertRoles(document, 'F-MARKETING*', ['Assignor'])
    self.assertRoles(document, self.user_id, ['Owner'])

class TestWebIllustration(TestSlapOSGroupRoleSecurityMixin):
  def test_MarketingFunction(self):
    document = self.portal.web_page_module.newContent(
        portal_type='Web Illustration')
    self.assertSecurityGroup(document,
        ['F-MARKETING*', self.user_id], False)
    self.assertRoles(document, 'F-MARKETING*', ['Assignor'])
    self.assertRoles(document, self.user_id, ['Owner'])


class TestSecurePaymentTool(TestSlapOSGroupRoleSecurityMixin):
  def test_SecurePaymentTool_no_permissions_for_users(self):
    tool = self.portal.portal_secure_payments
    self.assertPermissionsOfRole(tool, 'Anonymous', [])
    self.assertPermissionsOfRole(tool, 'Assignee', [])
    self.assertPermissionsOfRole(tool, 'Assignor', [])
    self.assertPermissionsOfRole(tool, 'Associate', [])
    self.assertPermissionsOfRole(tool, 'Auditor', [])
    self.assertPermissionsOfRole(tool, 'Authenticated', [])
    self.assertPermissionsOfRole(tool, 'Author', [])
    self.assertPermissionsOfRole(tool, 'Member', [])
    self.assertPermissionsOfRole(tool, 'Owner', [])
    self.assertPermissionsOfRole(tool, 'Reviewer', [])

    self.assertAcquiredPermissions(tool, ['Add ERP5 SQL Methods'])


class TestSaleSupplyModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SaleSupplyModule(self):
    module = self.portal.sale_supply_module
    # Why does the the sale_supply_module acquire the local roles
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-CUSTOMER', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSaleSupply(TestSlapOSGroupRoleSecurityMixin):
  def test_SaleSupply_default(self):
    supply = self.portal.sale_supply_module.newContent(
        portal_type='Sale Supply')
    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])

  def test_SaleSupply_DestinationCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)

    supply = self.portal.sale_supply_module.newContent(
        portal_type='Sale Supply')
    supply.edit(
        destination_value=person,
        )
    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])

    supply.validate()
    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', person.getUserId(), self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(supply, person.getUserId(), ['Auditor'])

    supply.invalidate()
    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])

  def test_SaleSupply_DestinationProject(self):
    project = self.addProject()
    supply = self.portal.sale_supply_module.newContent(
        portal_type='Sale Supply')
    supply.edit(
        destination_project_value=project,
        )

    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])

    supply.validate()

    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', project.getReference(), self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(supply, project.getReference(), ['Auditor'])

    supply.invalidate()
    self.assertSecurityGroup(supply,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(supply, self.user_id, ['Owner'])
    self.assertRoles(supply, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(supply, 'F-SALEMAN', ['Assignor'])


class TestProjectModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ProjectModule(self):
    module = self.portal.project_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', 'F-PRODUCTION*', 'F-CUSTOMER',
         'R-INSTANCE', 'R-COMPUTER', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestProject(TestSlapOSGroupRoleSecurityMixin):
  def test_Project_default(self):
    project = self.portal.project_module.newContent(
        portal_type='Project')
    # Local roles are recalculated at the end of the transaction
    transaction.commit()
    self.assertSecurityGroup(project,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*',
         project.getReference(), self.user_id], False)
    self.assertRoles(project, self.user_id, ['Owner'])
    self.assertRoles(project, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(project, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(project, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(project, project.getReference(), ['Auditor'])


class TestHostingSubscriptionModule(TestSlapOSGroupRoleSecurityMixin):
  def test_HostingSubscriptionModule(self):
    module = self.portal.hosting_subscription_module
    self.assertSecurityGroup(module,
        [module.Base_getOwnerId()], False)
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestHostingSubscription(TestSlapOSGroupRoleSecurityMixin):
  def test_HostingSubscription_default(self):
    hosting_subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription')
    self.assertSecurityGroup(hosting_subscription,
        [self.user_id], False)
    self.assertRoles(hosting_subscription, self.user_id, ['Owner'])


class TestSalePackingListModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SalePackingListModule(self):
    module = self.portal.sale_packing_list_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSalePackingList(TestSlapOSGroupRoleSecurityMixin):
  def test_SalePackingList_default(self):
    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

class TestConsumptionDeliveryModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ConsumptionDeliveryModule(self):
    module = self.portal.consumption_delivery_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestConsumptionDelivery(TestSlapOSGroupRoleSecurityMixin):
  def test_ConsumptionDelivery_default(self):
    delivery = self.portal.consumption_delivery_module.newContent(
        portal_type='Consumption Delivery')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

class TestOpenSaleOrderModule(TestSlapOSGroupRoleSecurityMixin):
  def test_OpenSaleOrderModule(self):
    module = self.portal.open_sale_order_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestOpenSaleOrder(TestSlapOSGroupRoleSecurityMixin):
  def test_OpenSaleOrder_default(self):
    delivery = self.portal.open_sale_order_module.newContent(
        portal_type='Open Sale Order')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

  def test_OpenSaleOrder_user(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    delivery = self.portal.open_sale_order_module.newContent(
        portal_type='Open Sale Order')

    delivery.edit(
      ledger='automated',
      destination_value=person
    )
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id, person.getUserId()], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, person.getUserId(), ['Auditor'])

    delivery.edit(
      ledger=None
    )
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

    delivery.edit(
      ledger='automated',
      destination_value=None
    )
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])


class TestSaleTradeConditionModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SaleTradeConditionModule(self):
    module = self.portal.sale_trade_condition_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', 'F-CUSTOMER',
         'R-SHADOW-PERSON', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSaleTradeCondition(TestSlapOSGroupRoleSecurityMixin):
  def test_SaleTradeCondition_default(self):
    delivery = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])

  def test_SaleTradeCondition_allUsers(self):
    delivery = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    delivery.validate()
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         'F-CUSTOMER', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])

    delivery.invalidate()
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])

  def test_SaleTradeCondition_singleUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    delivery = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    delivery.validate()
    delivery.edit(destination_value=person)
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id, person.getUserId()], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, person.getUserId(), ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])

    delivery.invalidate()
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])


  def test_SaleTradeCondition_project(self):
    project = self.portal.project_module.newContent(portal_type='Project')
    delivery = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    delivery.validate()
    delivery.edit(destination_project_value=project)
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id, project.getReference()], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, project.getReference(), ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])

    delivery.invalidate()
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])


class TestSubscriptionRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SubscriptionRequestModule(self):
    module = self.portal.subscription_request_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-CUSTOMER', 'F-ACCOUNTING*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSubscriptionRequest(TestSlapOSGroupRoleSecurityMixin):
  def test_SubscriptionRequest_default(self):
    delivery = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

  def test_SubscriptionRequest_automated_ledger(self):
    delivery = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')
    delivery.edit(ledger="automated")
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

  def test_SubscriptionRequest_user(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    delivery = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')
    delivery.edit(destination_decision_value=person, ledger="automated")
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id, "SHADOW-%s" % person.getUserId(),
           person.getUserId()], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, person.getUserId(), ['Associate'])
    self.assertRoles(delivery, "SHADOW-%s" % person.getUserId(), ['Auditor'])

  def test_SubscriptionRequest_organisation(self):
    # Ensure compatibility if destination_decision is an org
    reference = 'TESTORG-%s' % self.generateNewId()
    org = self.portal.organisation_module.newContent(
      portal_type='Organisation', reference=reference)
    delivery = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')
    delivery.edit(destination_decision_value=org, ledger="automated")
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])

class TestSubscriptionChangeRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test_SubscriptionChangeRequestModule(self):
    module = self.portal.subscription_change_request_module
    self.assertSecurityGroup(module,
        ['F-SALE*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestSubscriptionChangeRequest(TestSlapOSGroupRoleSecurityMixin):
  def test_SubscriptionChangeRequest_default(self):
    delivery = self.portal.subscription_change_request_module.newContent(
        portal_type='Subscription Change Request')
    self.assertSecurityGroup(delivery,
        [self.user_id, 'F-SALEAGT', 'F-SALEMAN'], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Auditor'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Auditor'])


class TestOrganisationModule(TestSlapOSGroupRoleSecurityMixin):
  def test_OrganisationModule(self):
    module = self.portal.organisation_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', 'R-SHADOW-PERSON',
         module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestOrganisation(TestSlapOSGroupRoleSecurityMixin):
  def test_Organisation_default(self):
    delivery = self.portal.organisation_module.newContent(
        portal_type='Organisation')
    self.assertSecurityGroup(delivery,
        ['F-ACCAGT', 'F-ACCMAN', 'F-SALEAGT', 'F-SALEMAN',
         'R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor'])


class TestBankAccount(TestSlapOSGroupRoleSecurityMixin):
  def test_BankAccount_default(self):
    delivery = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(portal_type="Bank Account")
    self.assertSecurityGroup(delivery,
        ['F-ACCAGT', 'F-ACCMAN', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])


class TestCashRegister(TestSlapOSGroupRoleSecurityMixin):
  def test_CashRegister_default(self):
    delivery = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(portal_type="Cash Register")
    self.assertSecurityGroup(delivery,
        ['F-ACCAGT', 'F-ACCMAN', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])


class TestBusinessProcessModule(TestSlapOSGroupRoleSecurityMixin):
  def test_BusinessProcessModule(self):
    module = self.portal.business_process_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*',
         module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestBusinessProcess(TestSlapOSGroupRoleSecurityMixin):
  def test_BusinessProcess_default(self):
    delivery = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])


class TestServiceModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ServiceModule(self):
    module = self.portal.service_module
    # XXX why does this module acquires local roles
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', 'F-CUSTOMER', 'F-PRODUCTION*',
         module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-SALE*', ['Auditor'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestService(TestSlapOSGroupRoleSecurityMixin):
  def test_Service_default(self):
    delivery = self.portal.service_module.newContent(
        portal_type='Service')
    self.assertSecurityGroup(delivery,
        ['F-SALE*', 'F-ACCOUNTING*', 'F-CUSTOMER', 'F-PRODUCTION*',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALE*', ['Auditor'])
    self.assertRoles(delivery, 'F-ACCOUNTING*', ['Auditor'])
    self.assertRoles(delivery, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(delivery, 'F-PRODUCTION*', ['Auditor'])


class TestPersonModule(TestSlapOSGroupRoleSecurityMixin):
  def test_PersonModule(self):
    module = self.portal.person_module
    self.assertSecurityGroup(module,
        ['F-SALE*', 'F-ACCOUNTING*', 'F-CUSTOMER', 'F-PRODUCTION*',
         'R-SHADOW-PERSON', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestPerson(TestSlapOSGroupRoleSecurityMixin):
  def test_Person_default(self):
    delivery = self.portal.person_module.newContent(
        portal_type='Person')
    self.assertSecurityGroup(delivery,
        ['F-ACCMAN', 'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])

  def test_Person_selfUser(self):
    delivery = self.portal.person_module.newContent(
        portal_type='Person')
    delivery.newContent(portal_type='ERP5 Login')
    self.assertSecurityGroup(delivery,
        ['F-ACCMAN', 'F-SALEAGT', 'F-ACCAGT', 'F-SALEMAN',
         delivery.getUserId(), 'SHADOW-%s' % delivery.getUserId(),
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])
    self.assertRoles(delivery, delivery.getUserId(), ['Assignee'])
    self.assertRoles(delivery, 'SHADOW-%s' % delivery.getUserId(), ['Auditor'])


class TestERP5Login(TestSlapOSGroupRoleSecurityMixin):
  def test_ERP5Login_selfUser(self):
    delivery = self.portal.person_module.newContent(
        portal_type='Person').newContent(portal_type='ERP5 Login')
    self.assertSecurityGroup(delivery,
        [delivery.getParentValue().getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, delivery.getParentValue().getUserId(), ['Assignee'])

class TestCertificateLogin(TestSlapOSGroupRoleSecurityMixin):
  def test_CertificateLogin_person(self):
    delivery = self.portal.person_module.newContent(
        portal_type='Person').newContent(portal_type='Certificate Login')
    self.assertSecurityGroup(delivery,
        [delivery.getParentValue().getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, delivery.getParentValue().getUserId(), ['Assignee'])

  def test_CertificateLogin_computeNode(self):
    delivery = self.portal.compute_node_module.newContent(
        portal_type='Compute Node').newContent(portal_type='Certificate Login')
    self.assertSecurityGroup(delivery,
        [delivery.getParentValue().getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, delivery.getParentValue().getUserId(), ['Assignee'])

  def test_CertificateLogin_computeNodeManager(self):
    project = self.portal.project_module.newContent(portal_type='Project')
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node')
    login = compute_node.newContent(portal_type='Certificate Login')
    compute_node.edit(follow_up_value=project)
    self.assertSecurityGroup(login,
        [compute_node.getUserId(), self.user_id,
         '%s_F-PRODAGNT' % project.getReference(),
         '%s_F-PRODMAN' % project.getReference()], False)
    self.assertRoles(login, self.user_id, ['Owner'])
    self.assertRoles(login, compute_node.getUserId(), ['Assignee'])
    self.assertRoles(login, '%s_F-PRODMAN' % project.getReference(), ['Assignor'])
    self.assertRoles(login, '%s_F-PRODAGNT' % project.getReference(), ['Assignee'])

  def test_CertificateLogin_softwareInstance(self):
    delivery = self.portal.software_instance_module.newContent(
        portal_type='Software Instance').newContent(portal_type='Certificate Login')
    self.assertSecurityGroup(delivery,
        [delivery.getParentValue().getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, delivery.getParentValue().getUserId(), ['Assignee'])

  def test_CertificateLogin_aggregateSoftwareInstance(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    partition = compute_node.newContent(portal_type='Compute Partition')
    delivery = self.portal.software_instance_module.newContent(
        portal_type='Software Instance').newContent(portal_type='Certificate Login')
    delivery.getParentValue().edit(aggregate_value=partition)
    self.assertSecurityGroup(delivery,
        [delivery.getParentValue().getUserId(),
         compute_node.getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, delivery.getParentValue().getUserId(), ['Assignee'])
    self.assertRoles(delivery, compute_node.getUserId(), ['Assignor'])


class TestDocumentIngestionModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DocumentIngestionModule(self):
    module = self.portal.document_ingestion_module
    # XXX Why does it acquire local roles
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', module.Base_getOwnerId()], True)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestDocumentModule(TestSlapOSGroupRoleSecurityMixin):
  def test_DocumentModule(self):
    module = self.portal.document_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestPDF(TestSlapOSGroupRoleSecurityMixin):

  def test_PDF_default(self):
    delivery = self.portal.document_module.newContent(
        portal_type='PDF')
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])

  def test_PDF_accounting(self):
    delivery = self.portal.document_module.newContent(
        portal_type='PDF',
        publication_section='accounting')
    self.assertSecurityGroup(delivery,
        ['F-ACCMAN', 'F-ACCAGT',
         self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-ACCMAN', ['Assignor'])
    self.assertRoles(delivery, 'F-ACCAGT', ['Assignee'])

  def test_PDF_report_contributor(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    delivery = self.portal.document_module.newContent(
        contributor_value=person,
        publication_section='report',
        portal_type='PDF')
    self.assertSecurityGroup(delivery,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, person.getUserId(), ['Associate'])

class TestText(TestSlapOSGroupRoleSecurityMixin):

  def test_Text_default(self):
    delivery = self.portal.document_module.newContent(
        portal_type='Text')
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])

  def test_Text_report_contributor(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    delivery = self.portal.document_module.newContent(
        publication_section='report',
        contributor_value=person,
        portal_type='Text')
    self.assertSecurityGroup(delivery,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, person.getUserId(), ['Associate'])

class TestSpreadsheet(TestSlapOSGroupRoleSecurityMixin):

  def test_Spreadsheet_default(self):
    delivery = self.portal.document_module.newContent(
        portal_type='Spreadsheet')
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])

  def test_Spreadsheet_report_contributor(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    delivery = self.portal.document_module.newContent(
        publication_section='report',
        contributor_value=person,
        portal_type='Spreadsheet')
    self.assertSecurityGroup(delivery,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, person.getUserId(), ['Associate'])

class TestQuery(TestSlapOSGroupRoleSecurityMixin):
  def test_Query_default(self):
    delivery = self.portal.query_module.newContent(
      portal_type='Query'
    )
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])

  def test_Query_agent(self):
    # There is no interaction workflow to recalculate local roles
    person = self.portal.person_module.newContent(portal_type='Person')
    delivery = self.portal.query_module.newContent(
      agent_value=person,
      portal_type='Query'
    )
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, person.getUserId(), [])


class TestNotificationMessageModule(TestSlapOSGroupRoleSecurityMixin):
  def test_NotificationMessageModule(self):
    module = self.portal.notification_message_module
    self.assertSecurityGroup(module,
        ['F-SALE*', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestNotificationMessage(TestSlapOSGroupRoleSecurityMixin):
  def test_NotificationMessage_default(self):
    delivery = self.portal.notification_message_module.newContent(
      portal_type='Notification Message'
    )
    self.assertSecurityGroup(delivery,
        ['F-SALEAGT', 'F-SALEMAN', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'F-SALEAGT', ['Assignee'])
    self.assertRoles(delivery, 'F-SALEMAN', ['Assignor'])


class TestCredentialUpdateModule(TestSlapOSGroupRoleSecurityMixin):
  def test_CredentialUpdateModule(self):
    module = self.portal.credential_update_module
    self.assertSecurityGroup(module,
        ['F-ACCOUNTING*', 'F-PRODUCTION*', module.Base_getOwnerId(),
         'F-CUSTOMER', 'F-SALE*'], False)
    self.assertRoles(module, 'F-ACCOUNTING*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-PRODUCTION*', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Auditor', 'Author'])
    self.assertRoles(module, 'F-SALE*', ['Auditor', 'Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestAccessTokenModule(TestSlapOSGroupRoleSecurityMixin):
  def test_AccessTokenModule(self):
    module = self.portal.access_token_module
    self.assertSecurityGroup(module,
        ['F-PRODUCTION*', 'F-CUSTOMER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'F-PRODUCTION*', ['Author'])
    self.assertRoles(module, 'F-CUSTOMER', ['Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestRestrictedAccessToken(TestSlapOSGroupRoleSecurityMixin):
  def test_RestrictedAccessToken_default(self):
    delivery = self.portal.access_token_module.newContent(
      portal_type='Restricted Access Token'
    )
    self.assertSecurityGroup(delivery,
        [self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])

  def test_RestrictedAccessToken_agent(self):
    # There is no interaction workflow to recalculate local roles
    person = self.portal.person_module.newContent(portal_type='Person')
    delivery = self.portal.access_token_module.newContent(
      agent_value=person,
      portal_type='Restricted Access Token'
    )
    self.assertSecurityGroup(delivery,
        [person.getUserId(), self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, person.getUserId(), ['Auditor'])


class TestConsumptionDocumentModule(TestSlapOSGroupRoleSecurityMixin):
  def test_ConsumptionDocumentModule(self):
    module = self.portal.consumption_document_module
    self.assertSecurityGroup(module,
        ['R-COMPUTER', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'R-COMPUTER', ['Author'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestIntegrationTool(TestSlapOSGroupRoleSecurityMixin):
  def test_IntegrationTool(self):
    module = self.portal.portal_integrations
    self.assertSecurityGroup(module,
        ['R-SHADOW-PERSON', module.Base_getOwnerId()], False)
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, module.Base_getOwnerId(), ['Owner'])


class TestIntegrationSite(TestSlapOSGroupRoleSecurityMixin):
  def test_IntegrationSite_default(self):
    delivery = self.portal.portal_integrations.newContent(
      portal_type='Integration Site'
    )
    self.assertSecurityGroup(delivery,
        ['R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(delivery, self.user_id, ['Owner'])
    self.assertRoles(delivery, 'R-SHADOW-PERSON', ['Auditor', 'Author'])

