# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2023  Nexedi SA and Contributors.
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

class TestSlapOSCoreMixin(SlapOSTestCaseMixinWithAbort):

  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.user_id = getSecurityManager().getUser().getId()

  def changeOwnership(self, document):
    """ Change the ownership of the document to the right and
        expected user. Normally the user which setups the site.
    """
    document.changeOwnership(getSecurityManager().getUser(), False)

  def createPerson(self):
    return self.portal.person_module.newContent(portal_type="Person")

  def createOrganisation(self):
    return self.portal.organisation_module.newContent(portal_type="Organisation")

  def createComputeNode(self, person):
    return self.portal.compute_node_module.newContent(
      portal_type='Compute Node',
      title=self.generateNewId(),
      reference="TESTNODE-%s" % self.generateNewId(),
      source_administration=person.getRelativeUrl())

  def createInstanceTree(self, person):
    return self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      title=self.generateNewId(),
      reference="TESTTREE-%s" % self.generateNewId(),
      destination_section=person.getRelativeUrl())

class TestERP5Type_acquireSecurityFromOwner(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()
    self.assertEqual({'Assignee': [self.user_id]},
      self.portal.ERP5Type_acquireSecurityFromOwner([], None, doc, None)) 

class TestPerson_getSecurityCategoryFromSelfShadow(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()

    self.assertEqual([],
      self.portal.Person_getSecurityCategoryFromSelfShadow([], None, None, None))

    self.assertEqual({'Auditor': ['SHADOW-%s' % (doc.getUserId())]},
      self.portal.Person_getSecurityCategoryFromSelfShadow([], None, doc, None)) 

class TestERP5Type_getSecurityCategoryFromParent(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()
    sub_doc = doc.newContent(portal_type="ERP5 Login")

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParent([], None, None, None))

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParent([], None, sub_doc, None)) 

    self.assertEqual([{'group': doc.getRelativeUrl()}],
      self.portal.ERP5Type_getSecurityCategoryFromParent(["group"], None, sub_doc, None)) 

    self.assertEqual([{'group': doc.getRelativeUrl()}, {'couscous': doc.getRelativeUrl()}],
      self.portal.ERP5Type_getSecurityCategoryFromParent(["group", "couscous"], None, sub_doc, None)) 

class TestERP5Type_getSecurityCategoryFromParentContent(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()
    org = self.createOrganisation()
    doc.edit(subordination=org.getRelativeUrl())
    sub_doc = doc.newContent(portal_type="ERP5 Login")

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParentContent([], None, None, None))

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParentContent([], None, sub_doc, None)) 

    self.assertEqual([{'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromParentContent(["subordination"], None, sub_doc, None)) 

    self.assertEqual([{'group': []}, {'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromParentContent(["group", "subordination"], None, sub_doc, None)) 

class TestERP5Type_getSecurityCategoryFromContentParent(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()
    org = self.createOrganisation()
    sub_org_document = org.newContent(portal_type="Address")
    doc.edit(subordination=sub_org_document.getRelativeUrl())

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromContentParent([], None, None, None))

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromContentParent([], None, doc, None)) 

    self.assertEqual([{'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromContentParent(["subordination"], None, doc, None)) 

    self.assertEqual([{'group': []}, {'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromContentParent(["group", "subordination"], None, doc, None)) 

class TestERP5Type_getSecurityCategoryFromParentContentParent(TestSlapOSCoreMixin):
  def test(self):
    doc = self.createPerson()
    sub_doc = doc.newContent(portal_type="ERP5 Login")
    org = self.createOrganisation()
    sub_org_document = org.newContent(portal_type="Address")
    doc.edit(subordination=sub_org_document.getRelativeUrl())

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParentContentParent([], None, None, None))

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromParentContentParent([], None, doc, None)) 

    self.assertEqual([{'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromParentContentParent(["subordination"], None, sub_doc, None)) 

    self.assertEqual([{'group': []}, {'subordination': [org.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromParentContentParent(["group", "subordination"], None, sub_doc, None)) 


class TestSoftwareInstance_getSecurityCategoryFromUser(TestSlapOSCoreMixin):
  def test(self):
    person = self.createPerson()
    instance_tree = self.portal.instance_tree_module.newContent(
      portal_type='Instance Tree',
      destination_section=person.getRelativeUrl())

    instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      specialise=instance_tree.getRelativeUrl())

    self.assertEqual([],
      self.portal.SoftwareInstance_getSecurityCategoryFromUser([], None, None, None))

    self.assertEqual([],
      self.portal.SoftwareInstance_getSecurityCategoryFromUser([], None, instance, None)) 

    self.assertEqual([{'destination_section': [person.getRelativeUrl()]}],
      self.portal.SoftwareInstance_getSecurityCategoryFromUser(["destination_section"], None, instance, None)) 

    self.assertEqual([{'couscous': [person.getRelativeUrl()]}, {'destination_section': [person.getRelativeUrl()]}],
      self.portal.SoftwareInstance_getSecurityCategoryFromUser(["couscous", "destination_section"], None, instance, None)) 


class TestPaymentTransaction_getSecurityCategoryFromUser(TestSlapOSCoreMixin):
  def test(self):
    person = self.createPerson()
    payment = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction', destination_section_value=person)

    self.assertEqual([],
      self.portal.PaymentTransaction_getSecurityCategoryFromUser([], None, None, None))

    self.assertEqual([],
      self.portal.PaymentTransaction_getSecurityCategoryFromUser([], None, payment, None)) 

    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertEqual({'Assignee': [shadow_user_id]},
      self.portal.PaymentTransaction_getSecurityCategoryFromUser(["destination_section"], None, payment, None)) 

    self.assertEqual({'Assignee': [shadow_user_id]},
      self.portal.PaymentTransaction_getSecurityCategoryFromUser(["couscous", "destination_section"], None, payment, None)) 

class TestPayzenEvent_getSecurityCategoryFromUserr(TestSlapOSCoreMixin):
  def test(self):
    person = self.createPerson()
    event = self.portal.system_event_module.newContent(
      portal_type='Payzen Event', destination_section_value=person)

    self.assertEqual([],
      self.portal.PayzenEvent_getSecurityCategoryFromUser([], None, None, None))

    self.assertEqual([],
      self.portal.PayzenEvent_getSecurityCategoryFromUser([], None, event, None)) 

    shadow_user_id = 'SHADOW-%s' % person.getUserId()
    self.assertEqual({'Assignee': [shadow_user_id]},
      self.portal.PayzenEvent_getSecurityCategoryFromUser(["destination_section"], None, event, None)) 

    self.assertEqual({'Assignee': [shadow_user_id]},
      self.portal.PayzenEvent_getSecurityCategoryFromUser(["couscous", "destination_section"], None, event, None)) 


class TestERP5Type_getSecurityCategoryFromChildAssignmentList(TestSlapOSCoreMixin):
  def test(self):
    person = self.createPerson()
    project = self.portal.project_module.newContent(
      portal_type="Project"
    )
    person.newContent(portal_type='Assignment',
      destination_project_value=project).open()

    self.assertEqual([],
      self.portal.ERP5Type_getSecurityCategoryFromChildAssignmentList([], None, None, None)) 

    self.assertEqual([{}],
      self.portal.ERP5Type_getSecurityCategoryFromChildAssignmentList([{}], None, person, None)) 

    self.assertEqual([{}],
      self.portal.ERP5Type_getSecurityCategoryFromChildAssignmentList(["destination_section"], None, person, None)) 

    self.assertEqual([{'destination_project': [project.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromChildAssignmentList(["destination_project"], None, person, None)) 
      
    self.assertEqual([{'destination_project': [project.getRelativeUrl()]}],
      self.portal.ERP5Type_getSecurityCategoryFromChildAssignmentList(
        ["destination_section", "destination_project"], None, person, None))

