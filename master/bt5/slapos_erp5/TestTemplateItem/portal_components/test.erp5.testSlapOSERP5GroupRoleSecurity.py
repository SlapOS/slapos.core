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

class TestSlapOSGroupRoleSecurityCoverage(SlapOSTestCaseMixinWithAbort):

  def testCoverage(self):
    """ Test which Portal types are not covered by this test.
    """
    test_source_code = self.portal.portal_components['test.erp5.testSlapOSERP5GroupRoleSecurity'].getTextContent()

    test_list = []
    for pt in self.portal.portal_types.objectValues():
      if len(pt.contentValues(portal_type="Role Information")) > 0:
        test_klass = "class Test%s" % "".join(pt.getId().split(" "))
        if test_klass not in test_source_code:
          test_list.append(test_klass)
    self.assertEqual(test_list, [])


class TestSlapOSGroupRoleSecurityMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.user_id = getSecurityManager().getUser().getId()

  def changeOwnership(self, document):
    """ Change the ownership of the document to the right and
        expected user. Normally the user which setups the site.
    """
    document.changeOwnership(getSecurityManager().getUser(), False)
    document.updateLocalRolesOnSecurityGroups()

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



class TestAssignment(TestSlapOSGroupRoleSecurityMixin):
  def test_Company_Group(self):
    assignment = self.portal.person_module.newContent(
        portal_type='Person').newContent(portal_type='Assignment')
    assignment.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(assignment,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(assignment, 'G-COMPANY', ['Auditor', 'Assignor'])
    self.assertRoles(assignment, self.user_id, ['Owner'])

class TestComputeNode(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        ['G-COMPANY', self.user_id, compute_node.getUserId()], False)
    self.assertRoles(compute_node, 'G-COMPANY', ['Assignor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_project=project.getRelativeUrl())
    self.login()

    self.tic()
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        ['G-COMPANY',  self.user_id, person.getUserId(),
         project.getReference(), compute_node.getUserId()], False)
    self.assertRoles(compute_node, 'G-COMPANY', ['Assignor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, person.getUserId(), ['Assignee'])
    self.assertRoles(compute_node, project.getReference(), ['Assignee'])

  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_section=organisation.getRelativeUrl())
    self.login()

    self.tic()
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        ['G-COMPANY',  self.user_id, person.getUserId(),
         organisation.getReference(), compute_node.getUserId()], False)
    self.assertRoles(compute_node, 'G-COMPANY', ['Assignor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, person.getUserId(), ['Assignee'])
    self.assertRoles(compute_node, organisation.getReference(), ['Assignee'])


  def test_ComputeNodeAgent(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        [self.user_id, 'G-COMPANY', person.getUserId(), compute_node.getUserId()], False)
    self.assertRoles(compute_node, 'G-COMPANY', ['Assignor'])
    self.assertRoles(compute_node, person.getUserId(), ['Assignee'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])

  def test_AllocationScope(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')

    # open/public
    compute_node.edit(allocation_scope='open/public')
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        [self.user_id, 'G-COMPANY', 'R-SHADOW-PERSON', compute_node.getUserId()], False)
    self.assertRoles(compute_node, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])

    # open/personal
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    compute_node.edit(allocation_scope='open/personal',
        source_administration=person.getRelativeUrl()
    )
    compute_node.updateLocalRolesOnSecurityGroups()
    shadow_user_id = 'SHADOW-%s' % person.getUserId()

    self.assertSecurityGroup(compute_node,
        [self.user_id, 'G-COMPANY', shadow_user_id,
         person.getUserId(), compute_node.getUserId()], False)
    self.assertRoles(compute_node, shadow_user_id, ['Auditor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])

    # open/friend
    friend_reference = 'TESTPERSON-%s' % self.generateNewId()
    friend_person = self.portal.person_module.newContent(portal_type='Person',
        reference=friend_reference)
    compute_node.edit(allocation_scope='open/friend',
        destination_section=friend_person.getRelativeUrl()
    )
    compute_node.updateLocalRolesOnSecurityGroups()
    shadow_friend_user_id = 'SHADOW-%s' % friend_person.getUserId()
    self.assertSecurityGroup(compute_node,
        [self.user_id, 'G-COMPANY', shadow_friend_user_id,
         person.getUserId(), compute_node.getUserId()], False)
    self.assertRoles(compute_node, shadow_friend_user_id, ['Auditor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])


  def test_selfComputeNode(self):
    reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node',
        reference=reference)
    compute_node.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(compute_node,
        [self.user_id, 'G-COMPANY', compute_node.getUserId()], False)
    self.assertRoles(compute_node, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(compute_node, self.user_id, ['Owner'])

class TestComputerModel(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    model = self.portal.computer_model_module.newContent(
        portal_type='Computer Model')
    model.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(model,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(model, 'G-COMPANY', ['Assignor'])
    self.assertRoles(model, self.user_id, ['Owner'])

  def test_ComputeNodeAgent(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    model = self.portal.computer_model_module.newContent(
        portal_type='Computer Model',
        source_administration=person.getRelativeUrl())
    model.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(model,
        ['G-COMPANY', self.user_id, person.getUserId()], False)
    self.assertRoles(model, person.getUserId(), ['Assignee'])
    self.assertRoles(model, self.user_id, ['Owner'])

class TestComputerModelModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.computer_model_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComputerModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.computer_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-MEMBER', 'R-SHADOW-PERSON', self.user_id],
        False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComputeNodeModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.compute_node_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-MEMBER', 'R-SHADOW-PERSON', self.user_id],
        False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComputerNetwork(TestSlapOSGroupRoleSecurityMixin):

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    network.ComputerNetwork_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()

    self.tic()
    network.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(network,
        ['G-COMPANY', 'R-SHADOW-PERSON', self.user_id, person.getUserId(),
         project.getReference()], False)
    self.assertRoles(network, 'G-COMPANY', ['Assignor'])
    self.assertRoles(network, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(network, self.user_id, ['Assignee', 'Owner'])
    self.assertRoles(network, person.getUserId(), ['Assignee'])
    self.assertRoles(network, project.getReference(), ['Assignee'])

  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    network.ComputerNetwork_createMovement(
      destination_section=organisation.getRelativeUrl())
    self.login()

    self.tic()
    network.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(network,
        ['G-COMPANY', 'R-SHADOW-PERSON', self.user_id, person.getUserId(),
         organisation.getReference()], False)
    self.assertRoles(network, 'G-COMPANY', ['Assignor'])
    self.assertRoles(network, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(network, self.user_id, ['Assignee', 'Owner'])
    self.assertRoles(network, person.getUserId(), ['Assignee'])
    self.assertRoles(network, organisation.getReference(), ['Assignee'])

  def test_GroupCompany(self):
    network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network')
    network.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(network,
        ['G-COMPANY', 'R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(network, 'G-COMPANY', ['Assignor'])
    self.assertRoles(network, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(network, self.user_id, ['Assignee', 'Owner'])


  def test_ComputeNodeAgent(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    network = self.portal.computer_network_module.newContent(
        portal_type='Computer Network',
        source_administration=person.getRelativeUrl())
    network.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(network,
        ['G-COMPANY', 'R-SHADOW-PERSON', self.user_id, person.getUserId()], False)
    self.assertRoles(network, person.getUserId(), ['Assignee'])
    self.assertRoles(network, self.user_id, ['Assignee', 'Owner'])

class TestComputerNetworkModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.computer_network_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', 'R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComputePartition(TestSlapOSGroupRoleSecurityMixin):
  def test_CustomerOfThePartition(self):
    partition = self.portal.compute_node_module.newContent(
        portal_type='Compute Node').newContent(portal_type='Compute Partition')
    self.portal.portal_workflow._jumpToStateFor(partition, 'busy')
    self.commit()

    instance_customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    slave_customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    instance_customer = self.portal.person_module.newContent(
        portal_type='Person', reference=instance_customer_reference)
    slave_customer = self.portal.person_module.newContent(
        portal_type='Person', reference=slave_customer_reference)

    instance_subscription_reference = 'TESTHS-%s' % self.generateNewId()
    instance_subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_subscription.edit(
        destination_section=instance_customer.getRelativeUrl(),
        reference=instance_subscription_reference)
    instance = self.portal.software_instance_module.template_software_instance\
        .Base_createCloneDocument(batch_mode=1)
    instance.edit(specialise=instance_subscription.getRelativeUrl(),
        aggregate=partition.getRelativeUrl())
    instance.validate()
    self.commit()

    slave_subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    slave_subscription.edit(
        destination_section=slave_customer.getRelativeUrl())
    slave = self.portal.software_instance_module.template_slave_instance\
        .Base_createCloneDocument(batch_mode=1)
    slave.validate()
    slave.edit(specialise=slave_subscription.getRelativeUrl(),
        aggregate=partition.getRelativeUrl())
    self.commit()

    partition.updateLocalRolesOnSecurityGroups()
    self.tic()
    self.assertSecurityGroup(partition,
        [self.user_id, instance_customer.getUserId(), slave_customer.getUserId(),
          instance_subscription_reference], True)
    self.assertRoles(partition, instance_customer.getUserId(), ['Auditor'])
    self.assertRoles(partition, slave_customer.getUserId(), ['Auditor'])
    self.assertRoles(partition, instance_subscription_reference, ['Auditor'])
    self.assertRoles(partition, self.user_id, ['Owner'])

  test_SoftwareInstanceGroupRelatedToComputePartition = \
      test_CustomerOfThePartition

class TestCredentialUpdateModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.credential_update_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        [self.user_id, 'R-MEMBER', 'G-COMPANY'], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDataSet(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    data_set = self.portal.data_set_module.newContent(portal_type='Data Set')
    data_set.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(data_set,
        [self.user_id, 'G-COMPANY'],
        False)
    self.assertRoles(data_set, 'G-COMPANY', ['Assignor'])
    self.assertRoles(data_set, self.user_id, ['Owner'])

class TestDataSetModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.data_set_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDocumentModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.document_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        [self.user_id, 'G-COMPANY'], False)
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestDrawing(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    drawing = self.portal.document_module.newContent(portal_type='Drawing')
    drawing.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(drawing,
        ['G-COMPANY', self.user_id,],  False)
    self.assertRoles(drawing, 'G-COMPANY', ['Assignor'])
    self.assertRoles(drawing, self.user_id, ['Owner'])

class TestFile(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    file_ = self.portal.document_module.newContent(portal_type='File')
    file_.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(file_,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(file_, 'G-COMPANY', ['Assignor'])
    self.assertRoles(file_, self.user_id, ['Owner'])

class TestInstanceTree(TestSlapOSGroupRoleSecurityMixin):
  def test_RelatedSoftwareInstanceGroup(self):
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference)
    subscription.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(subscription, [self.user_id, reference,
        'G-COMPANY'], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'G-COMPANY', ['Assignor'])

  def test_CustomOfTheInstanceTree(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference,
        destination_section=customer.getRelativeUrl())
    subscription.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(subscription, [self.user_id, reference,
        customer.getUserId(), 'G-COMPANY'], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, customer.getUserId(), ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'G-COMPANY', ['Assignor'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference,
        destination_section=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    subscription.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()

    self.tic()
    subscription.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(subscription, [self.user_id, reference,
        person.getUserId(), 'G-COMPANY', project.getReference()], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, person.getUserId(), ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'G-COMPANY', ['Assignor'])
    self.assertRoles(subscription, project.getReference(), ['Assignee'])


  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    reference = 'TESTHS-%s' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree', reference=reference,
        destination_section=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    subscription.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()

    self.tic()
    subscription.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(subscription, [self.user_id, reference,
        person.getUserId(), 'G-COMPANY', organisation.getReference()], False)
    self.assertRoles(subscription, reference, ['Assignee'])
    self.assertRoles(subscription, person.getUserId(), ['Assignee'])
    self.assertRoles(subscription, self.user_id, ['Owner'])
    self.assertRoles(subscription, 'G-COMPANY', ['Assignor'])
    self.assertRoles(subscription, organisation.getReference(), ['Assignee'])


class TestInstanceTreeModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.instance_tree_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-MEMBER', 'R-INSTANCE', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestImage(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    image = self.portal.image_module.newContent(portal_type='Image')
    image.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(image,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(image, 'G-COMPANY', ['Assignor'])
    self.assertRoles(image, self.user_id, ['Owner'])

class TestImageModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.image_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        [self.user_id, 'G-COMPANY'], False)
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestOrganisation(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation')
    organisation.setReference("TESTORG-%s" % self.generateNewId())
    organisation.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(organisation,
        ['G-COMPANY', self.user_id, organisation.getReference(), 'R-SHADOW-PERSON'], False)
    self.assertRoles(organisation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(organisation, organisation.getReference(), ['Assignee'])
    self.assertRoles(organisation, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(organisation, self.user_id, ['Owner', 'Assignee'])

  def test_without_reference(self):
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation')
    organisation.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(organisation,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(organisation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(organisation, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(organisation, self.user_id, ['Owner', 'Assignee'])

  def test_RoleAdmin(self):
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation')
    organisation.setReference("TESTORG-%s" % self.generateNewId())
    organisation.setRole("admin")
    organisation.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(organisation,
        ['G-COMPANY', self.user_id, organisation.getReference(), 'R-SHADOW-PERSON', 'R-MEMBER'], False)
    self.assertRoles(organisation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(organisation, organisation.getReference(), ['Assignee'])
    self.assertRoles(organisation, 'R-MEMBER', ['Auditor'])
    self.assertRoles(organisation, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(organisation, self.user_id, ['Owner', 'Assignee'])

  def test_defaultSlapOSOrganisation(self):
    # Test to ensure slapos organisation is well configured by default
    organisation = self.portal.organisation_module.slapos
    self.changeOwnership(organisation)
    organisation.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(organisation,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON', 'R-MEMBER'], False)
    self.assertRoles(organisation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(organisation, 'R-MEMBER', ['Auditor'])
    self.assertRoles(organisation, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(organisation, self.user_id, ['Owner', 'Assignee'])

class TestOrganisationModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.organisation_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-MEMBER', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestProjectModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.project_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-MEMBER', self.user_id, 'R-SHADOW-PERSON'], True)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestProject(TestSlapOSGroupRoleSecurityMixin):

  def test(self):
    project = self.portal.project_module.newContent(
        portal_type='Project')
    project.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(project,
        ['G-COMPANY', self.user_id, project.getReference(), 'R-SHADOW-PERSON'], False)
    self.assertRoles(project, 'G-COMPANY', ['Assignor'])
    self.assertRoles(project, project.getReference(), ['Assignee'])
    self.assertRoles(project, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(project, self.user_id, ['Owner', 'Assignee'])

class TestPDF(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    pdf = self.portal.document_module.newContent(portal_type='PDF')
    pdf.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(pdf,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(pdf, 'G-COMPANY', ['Assignor'])
    self.assertRoles(pdf, self.user_id, ['Owner'])

class TestPerson(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    person.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(person,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(person, 'G-COMPANY', ['Assignor'])
    self.assertRoles(person, self.user_id, ['Owner'])

  def test_TheUserHimself(self, login_portal_type="ERP5 Login"):
    person = self.portal.person_module.newContent(portal_type='Person')
    person.newContent(portal_type=login_portal_type)
    person.updateLocalRolesOnSecurityGroups()

    shadow_reference = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(person,
        ['G-COMPANY', self.user_id, person.getUserId(), shadow_reference], False)
    self.assertRoles(person, 'G-COMPANY', ['Assignor'])
    self.assertRoles(person, person.getUserId(), ['Assignee'])
    self.assertRoles(person, shadow_reference, ['Auditor'])
    self.assertRoles(person, self.user_id, ['Owner'])

  def test_TheUserHimself_Facebook(self):
    self.test_TheUserHimself(login_portal_type="Facebook Login")

  def test_TheUserHimself_Google(self):
    self.test_TheUserHimself(login_portal_type="Google Login")

  def test_TheUserHimself_Certificate(self):
    self.test_TheUserHimself(login_portal_type="Certificate Login")

  def test_ProjectMember(self, login_portal_type="ERP5 Login"):
    person = self.portal.person_module.newContent(portal_type='Person')
    person.newContent(portal_type=login_portal_type)
    project = self.portal.project_module.newContent(
      portal_type="Project"
    )
    project.validate()
    person.newContent(portal_type='Assignment',
      destination_project_value=project).open()
    self.tic()
    person.updateLocalRolesOnSecurityGroups()

    shadow_reference = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(person,
        ['G-COMPANY', self.user_id, person.getUserId(), shadow_reference, 
        project.getReference()], False)
    self.assertRoles(person, 'G-COMPANY', ['Assignor'])
    self.assertRoles(person, person.getUserId(), ['Assignee'])
    self.assertRoles(person, shadow_reference, ['Auditor'])
    self.assertRoles(person, project.getReference(), ['Auditor'])
    self.assertRoles(person, self.user_id, ['Owner'])



class TestERP5Login(TestSlapOSGroupRoleSecurityMixin):

  login_portal_type = "ERP5 Login"

  def test_PersonCanAccessLoginDocument(self):
    person = self.portal.person_module.newContent(portal_type='Person')
    login = person.newContent(portal_type=self.login_portal_type)
    person.updateLocalRolesOnSecurityGroups()
    login.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(login,
        [self.user_id, person.getUserId()], False)
    self.assertRoles(login, person.getUserId(), ['Assignee'])
    self.assertRoles(login, self.user_id, ['Owner'])

  def test_ComputeNodeCanAccessLoginDocument(self):
    compute_node = self.portal.compute_node_module.newContent(portal_type='Compute Node')
    login = compute_node.newContent(portal_type=self.login_portal_type)
    compute_node.updateLocalRolesOnSecurityGroups()
    login.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(login,
        [self.user_id, compute_node.getUserId()], False)
    self.assertRoles(login, compute_node.getUserId(), ['Assignee'])
    self.assertRoles(login, self.user_id, ['Owner'])

  def test_SoftwareInstanceCanAccessLoginDocument(self):
    software_instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
    login = software_instance.newContent(portal_type=self.login_portal_type)
    software_instance.updateLocalRolesOnSecurityGroups()
    login.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(login,
        [self.user_id, software_instance.getUserId()], False)
    self.assertRoles(login, software_instance.getUserId(), ['Assignee'])
    self.assertRoles(login, self.user_id, ['Owner'])

class TestCertificateLogin(TestERP5Login):
  login_portal_type = "Certificate Login"


class TestGoogleLogin(TestERP5Login):
  login_portal_type = "Google Login"
  def test_ComputeNodeCanAccessLoginDocument(self):
    # Not supported to add google login inside Compute Node
    pass
  
  def test_SoftwareInstanceCanAccessLoginDocument(self):
    # Not supported to add google login inside SoftwareInstance
    pass

class TestFacebookLogin(TestERP5Login):
  login_portal_type = "Facebook Login"
  def test_ComputeNodeCanAccessLoginDocument(self):
    # Not supported to add google login inside Compute Node
    pass
  
  def test_SoftwareInstanceCanAccessLoginDocument(self):
    # Not supported to add google login inside SoftwareInstance
    pass

class TestPersonModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.person_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestPresentation(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    presentation = self.portal.document_module.newContent(
        portal_type='Presentation')
    presentation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(presentation,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(presentation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(presentation, self.user_id, ['Owner'])

class TestSlaveInstance(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance')
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_CustomerOfTheInstance(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)

    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance', specialise=subscription.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_ProjectMember(self):
    customer = self.makePerson(user=1)
    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(customer.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance', specialise=instance_tree.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id, project.getReference()], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, project.getReference(), ['Assignee'])

  def test_OrganisationMember(self):
    customer = self.makePerson(user=1)
    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())    

    self.tic()
    self.login(customer.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()
    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance', specialise=instance_tree.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id, organisation.getReference()], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, organisation.getReference(), ['Assignee'])


  def test_SoftwareInstanceWhichProvidesThisSlaveInstance(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference=compute_node_reference)
    partition = compute_node.newContent(portal_type='Compute Partition')

    provider_reference = 'TESTSI-%s' % self.generateNewId()

    provider = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)

    provider.edit(reference=provider_reference,
        aggregate=partition.getRelativeUrl())
    provider.validate()

    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Slave Instance', aggregate=partition.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(instance, ['G-COMPANY', provider.getUserId(),
        compute_node.getUserId(), self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, provider.getUserId(), ['Assignor'])
    self.assertRoles(instance, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])

class TestSoftwareInstallation(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation')
    installation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(installation, [self.user_id,
        'G-COMPANY'], False)
    self.assertRoles(installation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(installation, self.user_id, ['Owner'])

  def test_ComputeNode(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference=compute_node_reference)

    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation',
        aggregate=compute_node.getRelativeUrl())
    installation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(installation, [self.user_id,
        'G-COMPANY', compute_node.getUserId()], False)
    self.assertRoles(installation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(installation, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(installation, self.user_id, ['Owner'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference=compute_node_reference,
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')
    
    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation',
        aggregate=compute_node.getRelativeUrl())
    installation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(installation, [self.user_id,
        'G-COMPANY', compute_node.getUserId(), project.getReference()], False)
    self.assertRoles(installation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(installation, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(installation, self.user_id, ['Owner'])
    self.assertRoles(installation, project.getReference(), ['Assignee'])

  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference=compute_node_reference,
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())    

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_section=organisation.getRelativeUrl())
    self.login()
    self.tic()
    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation',
        aggregate=compute_node.getRelativeUrl())
    installation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(installation, [self.user_id,
        'G-COMPANY', compute_node.getUserId(), organisation.getReference()], False)
    self.assertRoles(installation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(installation, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(installation, self.user_id, ['Owner'])
    self.assertRoles(installation, organisation.getReference(), ['Assignee'])


  def test_ProviderOfTheInstallation(self):
    provider_reference = 'TESTPERSON-%s' % self.generateNewId()
    provider = self.portal.person_module.newContent(
        portal_type='Person', reference=provider_reference)

    installation = self.portal.software_installation_module.newContent(
        portal_type='Software Installation',
        destination_section=provider.getRelativeUrl())
    installation.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(installation, [self.user_id,
        'G-COMPANY', provider.getUserId()], False)
    self.assertRoles(installation, 'G-COMPANY', ['Assignor'])
    self.assertRoles(installation, provider.getUserId(), ['Assignee'])
    self.assertRoles(installation, self.user_id, ['Owner'])

class TestSoftwareInstallationModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.software_installation_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', 'R-COMPUTER', self.user_id], False)
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSoftwareInstance(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance')
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_CustomerOfTheInstance(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)

    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance', specialise=subscription.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])

  def test_ProjectMember(self):
    customer = self.makePerson(user=1)

    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(customer.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance', specialise=instance_tree.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id, project.getReference()], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, project.getReference(), ['Assignee'])

  def test_OrganisationMember(self):
    customer = self.makePerson(user=1)
    subscription_reference = 'TESTHS-%s ' % self.generateNewId()
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference,
        destination_section=customer.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())    

    self.tic()
    self.login(customer.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()
    self.tic()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance', specialise=instance_tree.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', customer.getUserId(),
        subscription_reference, self.user_id, organisation.getReference()], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, customer.getUserId(), ['Assignee'])
    self.assertRoles(instance, subscription_reference, ['Assignee'])
    self.assertRoles(instance, self.user_id, ['Owner'])
    self.assertRoles(instance, organisation.getReference(), ['Assignee'])

  def test_ComputeNode(self):
    compute_node_reference = 'TESTCOMP-%s' % self.generateNewId()
    compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference=compute_node_reference)
    partition = compute_node.newContent(portal_type='Compute Partition')

    self.commit()

    instance = self.portal.software_instance_module.newContent(
        portal_type='Software Instance', aggregate=partition.getRelativeUrl())
    instance.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(instance, ['G-COMPANY', compute_node.getUserId(),
        self.user_id], False)
    self.assertRoles(instance, 'G-COMPANY', ['Assignor'])
    self.assertRoles(instance, compute_node.getUserId(), ['Assignor'])
    self.assertRoles(instance, self.user_id, ['Owner'])

class TestSoftwareInstanceModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.software_instance_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-COMPUTER', 'R-INSTANCE', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-COMPUTER', ['Auditor'])
    self.assertRoles(module, 'R-INSTANCE', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSoftwareProduct(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.software_product_module.newContent(
        portal_type='Software Product')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSoftwareProductModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.software_product_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSoftwareRelease(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    release = self.portal.software_release_module.newContent(
        portal_type='Software Release')
    release.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(release,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(release, 'G-COMPANY', ['Assignor'])
    self.assertRoles(release, self.user_id, ['Owner'])

class TestSoftwareReleaseModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.software_release_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSpreadsheet(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    spreadsheet = self.portal.document_module.newContent(
        portal_type='Spreadsheet')
    spreadsheet.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(spreadsheet,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(spreadsheet, 'G-COMPANY', ['Assignor'])
    self.assertRoles(spreadsheet, self.user_id, ['Owner'])

class TestText(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    text = self.portal.document_module.newContent(
        portal_type='Text')
    text.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(text,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(text, 'G-COMPANY', ['Assignor'])
    self.assertRoles(text, self.user_id, ['Owner'])

class TestContributionTool(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.portal_contributions
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        [self.user_id, 'G-COMPANY'], True)
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestOpenSaleOrderModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.open_sale_order_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestOpenSaleOrder(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.open_sale_order_module.newContent(
        portal_type='Open Sale Order')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSaleOrderModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.sale_order_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSaleOrder(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.sale_order_module.newContent(
        portal_type='Sale Order')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSalePackingListModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.sale_packing_list_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-MEMBER'], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])

class TestSalePackingList(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_GroupCustomerSubscription(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        destination_decision_value=person,
        specialise_value=self.portal.sale_trade_condition_module.\
                           slapos_subscription_trade_condition,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId()], False)
    self.assertRoles(product, 'G-COMPANY', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])

  def test_GroupCustomerAggregation(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        destination_decision_value=person,
        specialise_value=self.portal.sale_trade_condition_module.\
                           slapos_aggregated_trade_condition,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId()], False)
    self.assertRoles(product, 'G-COMPANY', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])

  def test_GroupCustomerAggregatedSubscription(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        destination_decision_value=person,
        specialise_value=self.portal.sale_trade_condition_module.\
                           slapos_aggregated_subscription_trade_condition,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId()], False)
    self.assertRoles(product, 'G-COMPANY', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])

class TestAccountingTransactionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.accounting_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON', 'R-MEMBER'], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Assignor'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestAccountingTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Accounting Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestBalanceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Balance Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestPaymentTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_ShadowUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(
        destination_section_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId(), shadow_user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, shadow_user_id, ['Auditor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_User(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.edit(
        destination_section_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId(),
         shadow_user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, shadow_user_id, ['Auditor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_User_without_destination_section(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Payment Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestPurchaseInvoiceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Purchase Invoice Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSaleInvoiceTransaction(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_User(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.accounting_module.newContent(
        portal_type='Sale Invoice Transaction')
    product.edit(
        destination_section_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, person.getUserId(), 
         'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestServiceModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.service_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-MEMBER'], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestService(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.service_module.newContent(
        portal_type='Service')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-MEMBER'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, 'R-MEMBER', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestAccountModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.account_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestAccount(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.account_module.newContent(
        portal_type='Account')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestCurrencyModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.currency_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON', 'R-MEMBER'], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestCurrency(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.currency_module.newContent(
        portal_type='Currency')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSaleTradeConditionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.sale_trade_condition_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-MEMBER', 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Assignor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSaleTradeCondition(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestAccountingPeriod(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(
        portal_type='Accounting Period')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestAcknowledgement(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.event_module.newContent(
        portal_type='Acknowledgement')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_SourceCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type='Acknowledgement',
        source_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_DestinationCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type='Acknowledgement',
        destination_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestBankAccount(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(
        portal_type='Bank Account')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestCampaignModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.campaign_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestCampaign(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.campaign_module.newContent(
        portal_type='Campaign')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestIncidentResponseModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.incident_response_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestIncidentResponse(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    incident_response = self.portal.incident_response_module.newContent(
        portal_type='Incident Response')
    incident_response.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(incident_response,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(incident_response, 'G-COMPANY', ['Assignor'])
    self.assertRoles(incident_response, self.user_id, ['Owner'])

class TestSubscriptionRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.subscription_request_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSubscriptionRequest(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    subscription_request = self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')
    subscription_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(subscription_request,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(subscription_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(subscription_request, self.user_id, ['Owner'])

class TestCashRegister(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(
        portal_type='Cash Register')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestComponentModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.component_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComponent(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.component_module.newContent(
        portal_type='Component')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestCreditCard(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.organisation_module.newContent(
        portal_type='Organisation').newContent(
        portal_type='Credit Card')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestDocumentIngestionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.document_ingestion_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestEventModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.event_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestGadget(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.portal_gadgets.newContent(
        portal_type='Gadget')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestGadgetTool(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.portal_gadgets
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestInventory(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.inventory_module.newContent(
        portal_type='Inventory')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestInventoryModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.inventory_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestKnowledgeBox(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.knowledge_pad_module.newContent(
        portal_type='Knowledge Pad').newContent(
        portal_type='Knowledge Box')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestKnowledgePad(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.knowledge_pad_module.newContent(
        portal_type='Knowledge Pad')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestKnowledgePadModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.knowledge_pad_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestMailMessage(TestSlapOSGroupRoleSecurityMixin):
  event_portal_type = 'Mail Message'
  def test_GroupCompany(self):
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type)
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_SourceCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        source_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_DestinationCustomer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        destination_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=compute_node.getRelativeUrl()
        )

    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        destination_value=person,
        follow_up=support_request.getRelativeUrl()
        )

    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', person.getUserId(),
         self.user_id, project.getReference()], False)
    self.assertRoles(event, 'G-COMPANY', ['Assignor'])
    self.assertRoles(event, person.getUserId(), ['Auditor'])
    self.assertRoles(event, project.getReference(), ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_ProjectMember_InstanceTreeRequest(self):

    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=instance_tree.getRelativeUrl()
        )

    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        destination_value=person,
        follow_up=support_request.getRelativeUrl()
        )

    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', person.getUserId(),
         self.user_id, project.getReference()], False)
    self.assertRoles(event, 'G-COMPANY', ['Assignor'])
    self.assertRoles(event, person.getUserId(), ['Auditor'])
    self.assertRoles(event, project.getReference(), ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])


  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_section=organisation.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=compute_node.getRelativeUrl()
        )

    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        destination_value=person,
        follow_up=support_request.getRelativeUrl()
        )

    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', person.getUserId(),
         self.user_id, organisation.getReference()], False)
    self.assertRoles(event, 'G-COMPANY', ['Assignor'])
    self.assertRoles(event, person.getUserId(), ['Auditor'])
    self.assertRoles(event, organisation.getReference(), ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_OrganisationMember_InstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=instance_tree.getRelativeUrl()
        )

    event = self.portal.event_module.newContent(
        portal_type=self.event_portal_type,
        destination_value=person,
        follow_up=support_request.getRelativeUrl()
        )

    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', person.getUserId(),
         self.user_id, organisation.getReference()], False)
    self.assertRoles(event, 'G-COMPANY', ['Assignor'])
    self.assertRoles(event, person.getUserId(), ['Auditor'])
    self.assertRoles(event, organisation.getReference(), ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])


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

class TestMeeting(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.meeting_module.newContent(
        portal_type='Meeting')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestMeetingModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.meeting_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestNotificationMessageModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.notification_message_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestNotificationMessage(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.notification_message_module.newContent(
        portal_type='Notification Message')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestProductModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.product_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestProduct(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.product_module.newContent(
        portal_type='Product')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestPurchaseOrderModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.purchase_order_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestPurchaseOrder(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.purchase_order_module.newContent(
        portal_type='Purchase Order')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestPurchaseTradeConditionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.purchase_trade_condition_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestPurchaseTradeCondition(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.purchase_trade_condition_module.newContent(
        portal_type='Purchase Trade Condition')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestQueryModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.query_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestQuery(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.query_module.newContent(
        portal_type='Query')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSaleOpportunityModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.sale_opportunity_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSaleOpportunity(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.sale_opportunity_module.newContent(
        portal_type='Sale Opportunity')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])
  
class TestSupportRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.support_request_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestSupportRequest(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request')
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])

  def test_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        )
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])

  def test_Template(self):
    support_request = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredSupportRequestTemplate())
    assert support_request.getPortalType() == 'Support Request'
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', support_request.Base_getOwnerId(), 'R-MEMBER'], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, support_request.Base_getOwnerId(), ['Owner'])
    self.assertRoles(support_request, 'R-MEMBER', ['Auditor'])
    self.assertPermissionsOfRole(support_request, 'Auditor',
        ['Access contents information', 'View'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=compute_node.getRelativeUrl()
        )
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', person.getUserId(), self.user_id, project.getReference()], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, project.getReference(), ['Auditor'])

  def test_ProjectMember_InstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=instance_tree.getRelativeUrl()
        )
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', person.getUserId(), self.user_id, project.getReference()], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, project.getReference(), ['Auditor'])


  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_section=organisation.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=compute_node.getRelativeUrl()
        )
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', person.getUserId(), self.user_id, organisation.getReference()], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, organisation.getReference(), ['Auditor'])

  def test_OrganisationMember_InstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())


    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()
    self.tic()

    support_request = self.portal.support_request_module.newContent(
        portal_type='Support Request',
        destination_decision_value=person,
        aggregate=instance_tree.getRelativeUrl()
        )
    support_request.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(support_request,
        ['G-COMPANY', person.getUserId(), self.user_id, organisation.getReference()], False)
    self.assertRoles(support_request, 'G-COMPANY', ['Assignor'])
    self.assertRoles(support_request, person.getUserId(), ['Auditor'])
    self.assertRoles(support_request, self.user_id, ['Owner'])
    self.assertRoles(support_request, organisation.getReference(), ['Auditor'])


class TestTransformationModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.transformation_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestTransformation(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.transformation_module.newContent(
        portal_type='Transformation')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestWebPageModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.web_page_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestWebPage(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.web_page_module.newContent(
        portal_type='Web Page')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestIntegrationTool(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.portal_integrations
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-SHADOW-PERSON', 'ERP5TypeTestCase', 'G-COMPANY'], False)
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'ERP5TypeTestCase', ['Owner'])

class TestIntegrationSite(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.portal_integrations
    self.changeOwnership(module)
    product = module.newContent(
        portal_type='Integration Site')
    self.assertSecurityGroup(product,
        ['R-SHADOW-PERSON', self.user_id, 'G-COMPANY'], False)
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor', 'Author'])
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestSystemEventModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.system_event_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-SHADOW-PERSON', self.user_id, 'G-COMPANY'], False)
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Author'])
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestPayzenEvent(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(event, 'G-COMPANY', ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_ShadowUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    event = self.portal.system_event_module.newContent(
        portal_type='Payzen Event')
    event.edit(
        destination_section_value=person,
        )
    event.updateLocalRolesOnSecurityGroups()
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(event,
        ['G-COMPANY', self.user_id, shadow_user_id], False)
    self.assertRoles(event, 'G-COMPANY', ['Auditor'])
    self.assertRoles(event, shadow_user_id, ['Assignee'])
    self.assertRoles(event, self.user_id, ['Owner'])

class TestWechatEvent(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    event = self.portal.system_event_module.newContent(
        portal_type='Wechat Event')
    event.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(event,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(event, 'G-COMPANY', ['Auditor'])
    self.assertRoles(event, self.user_id, ['Owner'])

  def test_ShadowUser(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    event = self.portal.system_event_module.newContent(
        portal_type='Wechat Event')
    event.edit(
        destination_section_value=person,
        )
    event.updateLocalRolesOnSecurityGroups()
    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertSecurityGroup(event,
        ['G-COMPANY', self.user_id, shadow_user_id], False)
    self.assertRoles(event, 'G-COMPANY', ['Auditor'])
    self.assertRoles(event, shadow_user_id, ['Assignee'])
    self.assertRoles(event, self.user_id, ['Owner'])

class TestSecurePaymentTool(TestSlapOSGroupRoleSecurityMixin):
  def test_no_permissions_for_users(self):
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

class TestBusinessProcessModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.business_process_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id, 'R-MEMBER'], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestBusinessProcess(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id, 'R-SHADOW-PERSON'], False)
    self.assertRoles(product, 'G-COMPANY', ['Auditor'])
    self.assertRoles(product, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestRegularisationRequestModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.regularisation_request_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestRegularisationRequest(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    product = self.portal.regularisation_request_module.newContent(
        portal_type='Regularisation Request',
        destination_decision_value=person,
        )
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, person.getUserId(), ['Auditor'])
    self.assertRoles(product, self.user_id, ['Owner'])

  def test_Template(self):
    product = self.portal.restrictedTraverse(
        self.portal.portal_preferences.getPreferredRegularisationRequestTemplate())
    assert product.getPortalType() == 'Regularisation Request'
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', product.Base_getOwnerId(), 'R-MEMBER'], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, product.Base_getOwnerId(), ['Owner'])
    self.assertRoles(product, 'R-MEMBER', ['Auditor'])
    self.assertPermissionsOfRole(product, 'Auditor',
        ['Access contents information', 'View'])

class TestInvitationTokenModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.invitation_token_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestContractInvitationToken(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.invitation_token_module.newContent(
        portal_type='Contract Invitation Token')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestAccessTokenModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.access_token_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], False)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestOneTimeRestrictedAccessToken(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.access_token_module.newContent(
        portal_type='One Time Restricted Access Token')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestRestrictedAccessToken(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    product = self.portal.access_token_module.newContent(
        portal_type='Restricted Access Token')
    product.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(product,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(product, 'G-COMPANY', ['Assignor'])
    self.assertRoles(product, self.user_id, ['Owner'])

class TestConsumptionDocumentModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.consumption_document_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['R-COMPUTER', 'R-MEMBER', self.user_id, 'G-COMPANY'], False)
    self.assertRoles(module, 'R-COMPUTER', ['Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestComputerConsumptionTioXMLFile(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    text = self.portal.consumption_document_module.newContent(
        portal_type='Computer Consumption TioXML File')

    self.assertSecurityGroup(text,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(text, 'G-COMPANY', ['Assignor'])
    self.assertRoles(text, self.user_id, ['Owner'])

class TestUserConsumptionHTMLFile(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    text = self.portal.consumption_document_module.newContent(
        portal_type='User Consumption HTML File')

    self.assertSecurityGroup(text,
        ['G-COMPANY', self.user_id],
        False)
    self.assertRoles(text, 'G-COMPANY', ['Assignor'])
    self.assertRoles(text, self.user_id, ['Owner'])

  def test_CustomerAssignee(self):
    customer_reference = 'TESTPERSON-%s' % self.generateNewId()
    customer = self.portal.person_module.newContent(
        portal_type='Person', reference=customer_reference)
    reference = 'TESTRC-%s' % self.generateNewId()
    html_document = self.portal.consumption_document_module.newContent(
        portal_type='User Consumption HTML File', reference=reference,
        contributor=customer.getRelativeUrl())
    html_document.updateLocalRolesOnSecurityGroups()

    self.assertSecurityGroup(html_document,
        ['G-COMPANY', customer.getUserId(), self.user_id], False)
    self.assertRoles(html_document, 'G-COMPANY', ['Assignor'])
    self.assertRoles(html_document, customer.getUserId(), ['Assignee'])
    self.assertRoles(html_document, self.user_id, ['Owner'])

class TestCloudContractModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.cloud_contract_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        [self.user_id, 'G-COMPANY', 'R-MEMBER', 'R-SHADOW-PERSON'], False)
    self.assertRoles(module, 'G-COMPANY', ['Author', 'Auditor'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor'])
    self.assertRoles(module, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestCloudContract(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    contract = self.portal.cloud_contract_module.newContent(
        portal_type='Cloud Contract')

    self.assertSecurityGroup(contract,
        ['G-COMPANY', 'R-SHADOW-PERSON', self.user_id],
        False)
    self.assertRoles(contract, 'G-COMPANY', ['Assignor'])
    self.assertRoles(contract, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(contract, self.user_id, ['Owner'])

  def test_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    contract = person.Person_generateCloudContract(batch=True)
    self.assertSecurityGroup(contract,
        ['G-COMPANY', person.getUserId(), 'R-SHADOW-PERSON', self.user_id], False)
    self.assertRoles(contract, 'G-COMPANY', ['Assignor'])
    self.assertRoles(contract, person.getUserId(), ['Auditor'])
    self.assertRoles(contract, 'R-SHADOW-PERSON', ['Auditor'])
    self.assertRoles(contract, self.user_id, ['Owner'])

class TestUpgradeDecisionModule(TestSlapOSGroupRoleSecurityMixin):
  def test(self):
    module = self.portal.upgrade_decision_module
    self.changeOwnership(module)
    self.assertSecurityGroup(module,
        ['G-COMPANY', 'R-MEMBER', self.user_id], True)
    self.assertRoles(module, 'G-COMPANY', ['Auditor', 'Author'])
    self.assertRoles(module, 'R-MEMBER', ['Auditor', 'Author'])
    self.assertRoles(module, self.user_id, ['Owner'])

class TestUpgradeDecision(TestSlapOSGroupRoleSecurityMixin):
  def test_GroupCompany(self):
    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision')
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', self.user_id], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])

  def test_Customer(self):
    reference = 'TESTPERSON-%s' % self.generateNewId()
    person = self.portal.person_module.newContent(portal_type='Person',
        reference=reference)
    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        destination_decision_value=person,
        )
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', person.getUserId(), self.user_id], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, person.getUserId(), ['Assignee'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])

  def test_ProjectMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        destination_decision_value=person)

    upgrade_decision.newContent(
        portal_type="Upgrade Decision Line",
        aggregate=compute_node.getRelativeUrl()
        )
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', person.getUserId(), self.user_id, project.getReference()], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, person.getUserId(), ['Assignee'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])
    self.assertRoles(upgrade_decision, project.getReference(), ['Assignee'])

  def test_ProjectMember_InstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    project = self.portal.project_module.newContent(
        portal_type='Project')

    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl())
    self.login()
    self.tic()

    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        destination_decision_value=person)
    upgrade_decision.newContent(
        portal_type="Upgrade Decision Line",
        aggregate=instance_tree.getRelativeUrl()
        )
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', person.getUserId(), self.user_id, project.getReference()], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, person.getUserId(), ['Assignee'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])
    self.assertRoles(upgrade_decision, project.getReference(), ['Assignee'])


  def test_OrganisationMember(self):
    person = self.makePerson(user=1)
    compute_node = self.portal.compute_node_module.newContent(
        portal_type='Compute Node',
        source_administration=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    compute_node.ComputeNode_createMovement(
      destination=person.getRelativeUrl(),
      destination_section=organisation.getRelativeUrl())
    self.login()
    self.tic()

    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        destination_decision_value=person)

    upgrade_decision.newContent(
        portal_type="Upgrade Decision Line",
        aggregate=compute_node.getRelativeUrl()
        )
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', person.getUserId(), self.user_id, organisation.getReference()], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, person.getUserId(), ['Assignee'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])
    self.assertRoles(upgrade_decision, organisation.getReference(), ['Assignee'])

  def test_OrganisationMember_InstanceTree(self):
    person = self.makePerson(user=1)
    instance_tree = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        destination_section=person.getRelativeUrl())
    organisation = self.portal.organisation_module.newContent(
        portal_type='Organisation',
        reference="TESTO-%s" % self.generateNewId())

    self.tic()
    self.login(person.getUserId())
    instance_tree.InstanceTree_createMovement(
      destination=organisation.getRelativeUrl())
    self.login()
    self.tic()

    upgrade_decision = self.portal.upgrade_decision_module.newContent(
        portal_type='Upgrade Decision',
        destination_decision_value=person)
    upgrade_decision.newContent(
        portal_type="Upgrade Decision Line",
        aggregate=instance_tree.getRelativeUrl()
        )
    upgrade_decision.updateLocalRolesOnSecurityGroups()
    self.assertSecurityGroup(upgrade_decision,
        ['G-COMPANY', person.getUserId(), self.user_id, organisation.getReference()], False)
    self.assertRoles(upgrade_decision, 'G-COMPANY', ['Assignor'])
    self.assertRoles(upgrade_decision, person.getUserId(), ['Assignee'])
    self.assertRoles(upgrade_decision, self.user_id, ['Owner'])
    self.assertRoles(upgrade_decision, organisation.getReference(), ['Assignee'])