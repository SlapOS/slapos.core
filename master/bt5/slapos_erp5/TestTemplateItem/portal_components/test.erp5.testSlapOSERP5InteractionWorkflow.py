# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, simulate

class TestSlapOSERP5InteractionWorkflowComputerSetAllocationScope(
    SlapOSTestCaseMixin):

  def _test_Computer_setAllocationScope_public(self,
                                              upgrade_scope=None,
                                              allocation_scope="open/public",
                                              source_administration=None,
                                              expected_upgrade_scope='auto'):
    computer = self.portal.computer_module.newContent(portal_type='Computer')

    computer.edit(capacity_scope=None,
                  monitor_scope=None,
                  upgrade_scope=upgrade_scope,
                  source_administration=source_administration)
    self.commit()
    computer.edit(allocation_scope=allocation_scope)

    self.commit()
    self.assertEqual(computer.getCapacityScope(), 'close')
    self.assertEqual(computer.getMonitorScope(), 'enabled')
    self.assertEqual(computer.getUpgradeScope(), expected_upgrade_scope)
    return computer

  def test_Computer_setAllocationScope_public_no_source_adm(self):
    self._test_Computer_setAllocationScope_public()

  def test_Computer_setAllocationScope_subscription_no_source_adm(self):
    self._test_Computer_setAllocationScope_public(
      allocation_scope="open/subscription"
    )

  def test_Computer_setAllocationScope_public_ask_confirmation(self):
    self._test_Computer_setAllocationScope_public(
      upgrade_scope="ask_confirmation")

  def test_Computer_setAllocationScope_subscription_ask_confirmation(self):
    self._test_Computer_setAllocationScope_public(
      allocation_scope="open/subscription",
      upgrade_scope="ask_confirmation"
    )

  def test_Computer_setAllocationScope_public_upgrade_disabled(self):
    self._test_Computer_setAllocationScope_public(
      upgrade_scope="disabled",
      expected_upgrade_scope="disabled")

  def test_Computer_setAllocationScope_subscription_upgrade_disabled(self):
    self._test_Computer_setAllocationScope_public(
      allocation_scope="open/subscription",
      upgrade_scope="disabled",
      expected_upgrade_scope="disabled")

  def test_Computer_setAllocationScope_public_with_source_adm(self):
    person = self.makePerson()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_public(
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [''])
    self.assertEqual(computer.getDestinationSection(), None)

  def test_Computer_setAllocationScope_subscription_with_source_adm(self):
    person = self.makePerson()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_public(
      source_administration=person.getRelativeUrl(),
      allocation_scope="open/subscription")

    self.assertEqual(computer.getSubjectList(), [''])
    self.assertEqual(computer.getDestinationSection(), None)


  def _test_Computer_setAllocationScope_personal(self,
                                              upgrade_scope=None,
                                              source_administration=None,
                                              subject_list=None):
    computer = self.portal.computer_module.newContent(portal_type='Computer',
                  capacity_scope=None,
                  monitor_scope=None,
                  upgrade_scope=upgrade_scope,
                  source_administration=source_administration)
    if subject_list:
      computer.setSubjectList(subject_list)
    self.commit()
    computer.edit(allocation_scope='open/personal')

    self.commit()
    self.assertEqual(computer.getCapacityScope(), 'open')
    self.assertEqual(computer.getMonitorScope(), 'disabled')
    return computer

  def test_Computer_setAllocationScope_personal(self):
    computer = self._test_Computer_setAllocationScope_personal()
    self.assertEqual(computer.getUpgradeScope(), 'ask_confirmation')
    self.assertEqual(computer.getSubjectList(), [])
    self.assertEqual(computer.getDestinationSection(), None)

  def test_Computer_setAllocationScope_personal_upgrade_disabled(self):
    computer = self._test_Computer_setAllocationScope_personal(
      upgrade_scope="disabled")
    self.assertEqual(computer.getUpgradeScope(), 'disabled')
    self.assertEqual(computer.getSubjectList(), [])
    self.assertEqual(computer.getDestinationSection(), None)

  def test_Computer_setAllocationScope_personal_upgrade_auto(self):
    computer = self._test_Computer_setAllocationScope_personal(
      upgrade_scope="auto")
    self.assertEqual(computer.getUpgradeScope(), 'auto')
    self.assertEqual(computer.getSubjectList(), [])
    self.assertEqual(computer.getDestinationSection(), None)

  def test_Computer_setAllocationScope_personal_with_source_adm(self):
    person = self.makePerson()
    self.tic()

    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])
    computer = self._test_Computer_setAllocationScope_personal(
      source_administration=person.getRelativeUrl(),
    )
    self.assertEqual(computer.getUpgradeScope(), 'ask_confirmation')
    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_Computer_setAllocationScope_personal_with_subject_list(self):
    person = self.makePerson()
    self.tic()

    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])
    computer = self._test_Computer_setAllocationScope_personal(
      source_administration=person.getRelativeUrl(),
      subject_list=["some@example.com"]
    )
    self.assertEqual(computer.getUpgradeScope(), 'ask_confirmation')
    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def _test_Computer_setAllocationScope_friend(self,
                                              upgrade_scope=None,
                                              source_administration=None,
                                              subject_list=None,
                                              expected_upgrade_scope='auto'):
    computer = self.portal.computer_module.newContent(portal_type='Computer')

    computer.edit(capacity_scope=None,
                  monitor_scope=None,
                  upgrade_scope=upgrade_scope,
                  source_administration=source_administration)

    if subject_list:
      computer.setSubjectList(subject_list)

    self.commit()
    computer.edit(allocation_scope='open/friend')

    self.commit()
    self.assertEqual(computer.getCapacityScope(), 'open')
    self.assertEqual(computer.getMonitorScope(), 'enabled')
    self.assertEqual(computer.getUpgradeScope(), expected_upgrade_scope)
    return computer

  def test_Computer_setAllocationScope_friend_no_source_adm(self):
    self._test_Computer_setAllocationScope_friend()

  def test_Computer_setAllocationScope_friend_ask_confirmation(self):
    self._test_Computer_setAllocationScope_friend(
      upgrade_scope="ask_confirmation")

  def test_Computer_setAllocationScope_friend_upgrade_disabled(self):
    self._test_Computer_setAllocationScope_friend(
      upgrade_scope="disabled",
      expected_upgrade_scope="disabled")

  def test_Computer_setAllocationScope_friend_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_friend(
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_Computer_setAllocationScope_friend_with_subject_list(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_friend(
      source_administration=person.getRelativeUrl(),
      subject_list=["some@example.com"]
    )

    self.assertSameSet(computer.getSubjectList(),
                      ['some@example.com', person.getDefaultEmailCoordinateText()])

    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])


  def _test_Computer_setAllocationScope_closed(self,
                                              upgrade_scope=None,
                                              source_administration=None,
                                              allocation_scope="close/forever",
                                              subject_list=None):
    computer = self.portal.computer_module.newContent(portal_type='Computer',
                  capacity_scope=None,
                  monitor_scope=None,
                  upgrade_scope=upgrade_scope,
                  source_administration=source_administration)
    if subject_list:
      computer.setSubjectList(subject_list)
    self.commit()
    computer.edit(allocation_scope=allocation_scope)

    self.commit()
    self.assertEqual(computer.getCapacityScope(), 'close')
    self.assertEqual(computer.getMonitorScope(), 'disabled')
    self.assertEqual(computer.getUpgradeScope(), upgrade_scope)
    return computer


  def test_Computer_setAllocationScope_closed_forever_no_source_adm(self):
    self._test_Computer_setAllocationScope_closed()

  def test_Computer_setAllocationScope_closed_forever_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_closed(
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_Computer_setAllocationScope_closed_termination_no_source_adm(self):
    self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/termination",
    )

  def test_Computer_setAllocationScope_closed_termination_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/termination",
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_Computer_setAllocationScope_closed_outdated_no_source_adm(self):
    self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/outdated",
    )

  def test_Computer_setAllocationScope_closed_outdated_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/outdated",
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])

  def test_Computer_setAllocationScope_closed_maintenance_no_source_adm(self):
    self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/maintenance",
    )

  def test_Computer_setAllocationScope_closed_maintenance_with_source_adm(self):
    person = self.makePerson()
    self.tic()
    self.assertNotIn(person.getDefaultEmailCoordinateText(), [None, ""])

    computer = self._test_Computer_setAllocationScope_closed(
      allocation_scope="close/maintenance",
      source_administration=person.getRelativeUrl())

    self.assertEqual(computer.getSubjectList(), [person.getDefaultEmailCoordinateText()])
    self.assertEqual(computer.getDestinationSectionList(),
     [person.getRelativeUrl()])


class TestSlapOSERP5InteractionWorkflowComputerNetworkSetReference(
    SlapOSTestCaseMixin):
  
  def test_ComputerNetwork_validate(self):
    computer_network = self.portal.computer_network_module.newContent(
      portal_type="Computer Network"
    )
    self.commit()
    self.assertNotEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "validated")
    self.assertEqual(computer_network.getSourceAdministration(), None)

  @simulate("ComputerNetwork_init", "*args, **kwargs", "return")
  def test_ComputerNetwork_validate_manual(self):

    computer_network = self.portal.computer_network_module.newContent(
      portal_type="Computer Network"
    )
    self.commit()
    self.assertEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "draft")
    self.assertEqual(computer_network.getSourceAdministration(), None)

    computer_network.setReference(
      "COMPNTEST-%s" % self.new_id
    )
    self.tic()
    self.assertNotEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "validated")
    self.assertEqual(computer_network.getSourceAdministration(), None)

  @simulate("ComputerNetwork_init", "*args, **kwargs", "return")
  def test_ComputerNetwork_validate_manual_with_user(self):
    person = self.makePerson(user=True)

    self.login(person.getUserId())
    computer_network = self.portal.computer_network_module.newContent(
      portal_type="Computer Network"
    )
    self.commit()
    self.assertEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "draft")
    self.assertEqual(computer_network.getSourceAdministration(), None)

    computer_network.setReference(
      "COMPNTEST-%s" % self.new_id
    )
    self.tic()
    self.assertNotEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "validated")
    self.assertEqual(computer_network.getSourceAdministration(),
      person.getRelativeUrl())

  @simulate("ComputerNetwork_init", "*args, **kwargs", "return")
  def test_ComputerNetwork_validate_manual_already_validated(self):
    person = self.makePerson(user=True)

    self.login(person.getUserId())
    computer_network = self.portal.computer_network_module.newContent(
      portal_type="Computer Network"
    )
    computer_network.validate()
    self.commit()
    self.assertEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "validated")
    self.assertEqual(computer_network.getSourceAdministration(), None)

    computer_network.setReference(
      "COMPNTEST-%s" % self.new_id
    )
    self.tic()
    self.assertNotEqual(computer_network.getReference(), None)
    self.assertEqual(computer_network.getValidationState(), "validated")
    self.assertEqual(computer_network.getSourceAdministration(),
      None)

class TestSlapOSERP5InteractionWorkflowProjectSetDestination(
    SlapOSTestCaseMixin):

  def test_Project_validateAndAssign(self):
    person = self.makePerson()
    self.tic()

    project = self.portal.project_module.newContent(
      portal_type="Project"
    )
    project.setDestinationDecisionValue(person)
    self.commit()

    self.assertEqual(project.getValidationState(), "validated")
    self.assertNotEqual(project.getStartDate(), None)
    self.assertNotEqual(project.getReference(), None)
    self.assertTrue(project.getReference().startswith("PROJ-"), 
      "%s don't start with PROJ-" % project.getReference())
    
  def test_Project_validateAndAssign_with_owner(self):
    person = self.makePerson(user=1)
    self.tic()

    assignment_amount = len(person.objectValues(portal_type="Assignment"))
    self.login(person.getUserId())
    project = self.portal.project_module.newContent(
      portal_type="Project"
    )
    project.setDestinationDecisionValue(person)
    self.commit()
    self.assertEqual(project.getValidationState(), "validated")
    self.assertNotEqual(project.getStartDate(), None)
    self.assertNotEqual(project.getReference(), None)
    self.assertTrue(project.getReference().startswith("PROJ-"), 
      "%s don't start with PROJ-" % project.getReference())
    
    self.assertEqual(assignment_amount + 1,
     len(person.objectValues(portal_type="Assignment")))

    self.assertNotEqual([],
      [i for i in person.objectValues(portal_type="Assignment")
        if (i.getDestinationProjectValue() == project and i.getValidationState() == "open")])

  def test_Project_validateAndAssign_with_assignment(self):
    person = self.makePerson(user=1)
    self.tic()

    assignment_amount = len(person.objectValues(portal_type="Assignment"))
    self.login(person.getUserId())
    project = self.portal.project_module.newContent(
      portal_type="Project"
    )
    person.newContent(
      title="Assigment for Project %s" % project.getTitle(),
      portal_type="Assignment",
      destination_project_value=project)
    self.tic()
    project.setDestinationDecisionValue(person)
    self.commit()
    self.assertEqual(project.getValidationState(), "validated")
    self.assertNotEqual(project.getStartDate(), None)
    self.assertNotEqual(project.getReference(), None)
    self.assertTrue(project.getReference().startswith("PROJ-"), 
      "%s don't start with PROJ-" % project.getReference())
    
    self.assertEqual(assignment_amount + 1,
     len(person.objectValues(portal_type="Assignment")))

    self.assertNotEqual([],
      [i for i in person.objectValues(portal_type="Assignment")
        if (i.getDestinationProjectValue() == project and i.getValidationState() == "open")])


class TestSlapOSERP5InteractionWorkflowOrganisationSetRole(
    SlapOSTestCaseMixin):

  def test_Organisation_validateAndAssign(self):
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    organisation.setRole("host")
    self.commit()

    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertNotEqual(organisation.getReference(), None)
    self.assertTrue(organisation.getReference().startswith("SITE-"), 
      "%s don't start with SITE-" % organisation.getReference())

  def test_Organisation_validateAndAssign_client(self):
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    organisation.setRole("client")
    self.commit()

    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertNotEqual(organisation.getReference(), None)
    self.assertTrue(organisation.getReference().startswith("O-"), 
      "%s don't start with O-" % organisation.getReference())

  def test_Organisation_validateAndAssign_other(self):
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    organisation.setRole("other")
    self.commit()

    self.assertEqual(organisation.getValidationState(), "draft")
    self.assertFalse(organisation.getReference("").startswith("O-"), 
      "%s start with O-" % organisation.getReference())
    self.assertFalse(organisation.getReference("").startswith("SITE-"), 
      "%s start with SITE-" % organisation.getReference())

  def test_Organisation_validateAndAssign_with_owner(self):
    person = self.makePerson(user=1)
    self.tic()

    assignment_amount = len(person.objectValues(portal_type="Assignment"))
    self.login(person.getUserId())
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    organisation.setRole("host")
    self.commit()
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertNotEqual(organisation.getReference(), None)
    self.assertTrue(organisation.getReference().startswith("SITE-"), 
      "%s don't start with SITE-" % organisation.getReference())
    
    self.assertEqual(assignment_amount + 1,
     len(person.objectValues(portal_type="Assignment")))

    self.assertNotEqual([],
      [i for i in person.objectValues(portal_type="Assignment")
        if (i.getDestinationValue() == organisation and i.getValidationState() == "open")])

  def test_Organisation_validateAndAssign_with_assignment(self):
    person = self.makePerson(user=1)
    self.tic()

    assignment_amount = len(person.objectValues(portal_type="Assignment"))
    self.login(person.getUserId())
    organisation = self.portal.organisation_module.newContent(
      portal_type="Organisation"
    )
    person.newContent(
      title="Assigment for Organisation %s" % organisation.getTitle(),
      portal_type="Assignment",
      subordination_value=organisation)
    self.tic()
    organisation.setRole("host")
    self.commit()
    self.assertEqual(organisation.getValidationState(), "validated")
    self.assertNotEqual(organisation.getReference(), None)
    self.assertTrue(organisation.getReference().startswith("SITE-"), 
      "%s don't start with SITE-" % organisation.getReference())
    
    self.assertEqual(assignment_amount + 1,
     len(person.objectValues(portal_type="Assignment")))

    self.assertNotEqual([],
      [i for i in person.objectValues(portal_type="Assignment")
        if (i.getSubordinationValue() == organisation and i.getValidationState() == "open")])


