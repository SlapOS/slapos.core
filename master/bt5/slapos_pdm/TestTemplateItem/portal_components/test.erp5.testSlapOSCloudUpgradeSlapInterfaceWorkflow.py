# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2012 Nexedi SA and Contributors. All Rights Reserved.
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
#from zExceptions import Unauthorized
import transaction

class TestSlapOSCoreProjectSlapInterfaceWorkflow(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    portal = self.getPortalObject()
    
    person_user = self.makePerson()
    self.tic()
    
    self.login()
    self.compute_node = self.portal.compute_node_module.template_compute_node\
        .Base_createCloneDocument(batch_mode=1)
    new_id = self.generateNewId()
    self.compute_node.edit(
      title="compute node %s" % (new_id, ),
      reference="TESTCOMP-%s" % (new_id, ),
      source_administration=person_user.getRelativeUrl()
    )
    self.compute_node.validate()

    self.upgrade_decision = portal.upgrade_decision_module.newContent(
      portal_type="Upgrade Decision",
    )

    # Value set by the init
    self.assertTrue(self.upgrade_decision.getReference().startswith("UD-"),
      "Reference don't start with UD- : %s" % self.upgrade_decision.getReference())

    self.software_release = self._makeSoftwareRelease()
    self.tic()

  def _addUpgradeLine(self, aggregate):
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate_value_list=[self.software_release,
                 aggregate]
    )

  def beforeTearDown(self):
    transaction.abort()

  def test_upgrade_decision_approveRegistration_no_line(self):
    self.assertRaises(ValueError, self.upgrade_decision.approveRegistration)

  def test_upgrade_decision_approveRegistration_no_aggregate(self):
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate=self.software_release.getRelativeUrl()
    )
    self.assertRaises(ValueError, self.upgrade_decision.approveRegistration)

  def test_upgrade_decision_approveRegistration_no_upgrade_scope(self):
    self._addUpgradeLine(self.compute_node)
    self.assertRaises(TypeError, self.upgrade_decision.approveRegistration)

  def test_upgrade_decision_approveRegistration_computer(self):
    self._addUpgradeLine(self.compute_node)
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    # Call again does nothing
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    self.tic()
    # Call again does nothing again
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

  def test_upgrade_decision_approveRegistration_instance_tree(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    # Call again does nothing
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    self.tic()
    # Call again does nothing again
    self.upgrade_decision.approveRegistration(
      upgrade_scope="ask_confirmation"
    )
    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))


  def test_upgrade_decision_approveRegistration_computer_auto(self):
    self._addUpgradeLine(self.compute_node)
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    # Call again does nothing
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    self.tic()
    # Call again does nothing again
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.compute_node.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

  def test_upgrade_decision_approveRegistration_instance_tree_auto(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    # Call again does nothing
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

    self.tic()
    # Call again does nothing again
    # Call again does nothing
    self.upgrade_decision.approveRegistration(
      upgrade_scope="auto"
    )
    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())
    
    self.commit()
    tag = "%s_requestUpgradeDecisionCreation_inProgress" % self.instance_tree.getUid()
    self.assertEqual(2,
      self.portal.portal_activities.countMessageWithTag(tag))

  def test_upgrade_decision_reviewRegistration_no_software_release_url(self):
    self.assertRaises(TypeError, self.upgrade_decision.reviewRegistration)

  def test_upgrade_decision_reviewRegistration_draft(self):
    # Do nothing as draft
    software_release = self.generateNewSoftwareReleaseUrl()
    self.upgrade_decision.reviewRegistration(software_release_url=software_release)

  def test_upgrade_decision_reviewRegistration(self):
    self._addUpgradeLine(self.compute_node)
    software_release = self.generateNewSoftwareReleaseUrl()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.plan()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("cancelled",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_confirm(self):
    self._addUpgradeLine(self.compute_node)
    software_release = self.generateNewSoftwareReleaseUrl()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.confirm()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("cancelled",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_rejected(self):
    self._addUpgradeLine(self.compute_node)
    software_release = self.generateNewSoftwareReleaseUrl()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.reject()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("rejected",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_same_url(self):
    self._addUpgradeLine(self.compute_node)

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.plan()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("planned",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_confirm_same_url(self):
    self._addUpgradeLine(self.compute_node)
    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.confirm()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("confirmed",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_rejected_same_url(self):
    self._addUpgradeLine(self.compute_node)

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.reject()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.software_release.getUrlString())

    self.assertEqual("rejected",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_started(self):
    self._addUpgradeLine(self.compute_node)
    software_release = self.generateNewSoftwareReleaseUrl()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.plan()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=software_release)

    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_instance_tree(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.plan()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("cancelled",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_instance_tree_confirmed(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.confirm()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("cancelled",
      self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_reviewRegistration_instance_tree_started(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("draft",
      self.upgrade_decision.getSimulationState())

    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.reviewRegistration(
      software_release_url=self.instance_tree.getUrlString())

    self.assertEqual("started",
      self.upgrade_decision.getSimulationState())

  @simulate('InstanceTree_isUpgradePossible',
            'software_release_url', 'return 1')
  def test_upgrade_decision_requestUpgrade_instance_tree(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)
    self.tic()
   
    slap_state = self.instance_tree.getSlapState()
    
    self.upgrade_decision.requestUpgrade()
    self.assertNotEqual(self.software_release.getUrlString(),
                        self.instance_tree.getUrlString())

    self.upgrade_decision.confirm()
    self.upgrade_decision.start()

    # Check that url_string change, but slap state doesn't
    self.assertNotEqual(self.software_release.getUrlString(),
                        self.instance_tree.getUrlString())

    self.upgrade_decision.requestUpgrade()
    self.assertEqual(self.software_release.getUrlString(),
                    self.instance_tree.getUrlString())


    self.assertEqual(slap_state, self.instance_tree.getSlapState())
    self.assertEqual('stopped', self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_requestUpgrade_instance_tree_no_software_release(self):
    self._makeTree()
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate_value_list=[self.instance_tree]
    )
    
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.requestUpgrade()
    self.assertEqual('started', self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_requestUpgrade_compute_node_no_software_release(self):
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate_value_list=[self.compute_node]
    )
    
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.requestUpgrade()
    self.assertEqual('started', self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_requestUpgrade_only_software_release(self):
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate_value_list=[self.software_release]
    )
    
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.requestUpgrade()
    self.assertEqual('started', self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_requestUpgrade_duplicated(self):
    self._makeTree()
    self.upgrade_decision.newContent(
      portal_type="Upgrade Decision Line",
      aggregate_value_list=[
        self.software_release,
        self.instance_tree,
        self.compute_node]
    )
    
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.assertRaises(ValueError, self.upgrade_decision.requestUpgrade)
    self.assertEqual('started', self.upgrade_decision.getSimulationState())

  def test_upgrade_decision_requestUpgrade_compute_node(self):
    self._addUpgradeLine(self.compute_node)
    
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.requestUpgrade()
    self.tic()

    self.assertEqual('stopped', self.upgrade_decision.getSimulationState())
    software_installation = self.compute_node.getAggregateRelatedValue(
            portal_type='Software Installation')
    self.assertEqual('start_requested', software_installation.getSlapState())
    self.assertEqual(self.software_release.getUrlString(),
      software_installation.getUrlString())
    self.assertEqual('validated', software_installation.getValidationState())

  @simulate('InstanceTree_isUpgradePossible',
            'software_release_url', 'return 0')
  def test_upgrade_decision_requestUpgrade_instance_tree_not_possible(self):
    self._makeTree()
    self._addUpgradeLine(self.instance_tree)

    self.assertNotEqual(self.instance_tree.getUrlString(),
      self.software_release.getUrlString())

    slap_state = self.instance_tree.getSlapState()
    self.upgrade_decision.confirm()
    self.upgrade_decision.start()
    self.tic()

    self.upgrade_decision.requestUpgrade()
    self.tic()

    self.assertEqual('started', self.upgrade_decision.getSimulationState())
    self.assertNotEqual(self.instance_tree.getUrlString(),
      self.software_release.getUrlString())

    self.assertEqual(slap_state,
      self.instance_tree.getSlapState())

