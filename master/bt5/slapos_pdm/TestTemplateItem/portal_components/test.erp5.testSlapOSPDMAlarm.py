# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSUpgradeDecisionProcess(SlapOSTestCaseMixin):
  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.new_id = self.generateNewId()

  def _makeUpgradeDecision(self, confirm=True):
    upgrade_decision = self.portal.\
       upgrade_decision_module.newContent(
         portal_type="Upgrade Decision",
         title="TESTUPDE-%s" % self.new_id)
    if confirm:
      upgrade_decision.confirm()
    return upgrade_decision

  def _makeInstanceTree(self, slap_state="start_requested"):
    instance_tree = self.portal\
      .instance_tree_module.template_instance_tree\
      .Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    instance_tree.edit(
        title= "Test hosting sub start %s" % self.new_id,
        reference="TESTHSS-%s" % self.new_id,
    )
    self.portal.portal_workflow._jumpToStateFor(instance_tree, slap_state)

    return instance_tree

  def test_alarm_upgrade_decision_process_instance_tree(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_started,
      upgrade_decision,
      'UpgradeDecision_processUpgrade')

  def test_alarm_upgrade_decision_process_planned(self):
    upgrade_decision = self._makeUpgradeDecision(confirm=0)
    upgrade_decision.plan()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_planned,
      upgrade_decision,
      'UpgradeDecision_notify')

  def test_alarm_upgrade_decision_process_stopped(self):
    upgrade_decision = self._makeUpgradeDecision()
    upgrade_decision.start()
    upgrade_decision.stop()
    self.tic()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_upgrade_decision_process_stopped,
      upgrade_decision,
      'UpgradeDecision_notifyDelivered')

  def _test_alarm_compute_node_create_upgrade_decision(self, allocation_scope, upgrade_scope):
    compute_node = self._makeComputeNode(allocation_scope=allocation_scope)[0]
    compute_node.setUpgradeScope(upgrade_scope)
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_compute_node_create_upgrade_decision,
      compute_node,
      'ComputeNode_checkAndCreateUpgradeDecision')

  def _test_alarm_compute_node_create_upgrade_decision_not_visited(self, allocation_scope, upgrade_scope):
    compute_node = self._makeComputeNode(allocation_scope=allocation_scope)[0]
    compute_node.setUpgradeScope(upgrade_scope)
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_pdm_compute_node_create_upgrade_decision,
      compute_node,
      'ComputeNode_checkAndCreateUpgradeDecision')


  def test_alarm_compute_node_create_upgrade_decision_auto(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/public', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('open/personal', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('open/subscription', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('close/outdated', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('close/maintanance', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('close/termination', 'auto')
    self._test_alarm_compute_node_create_upgrade_decision('close/noallocation', 'auto')

  def test_alarm_compute_node_create_upgrade_decision_ask_confirmation(self):
    self._test_alarm_compute_node_create_upgrade_decision('open/public', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('open/personal', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('open/subscription', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('close/outdated', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('close/maintanance', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('close/termination', 'confirmation')
    self._test_alarm_compute_node_create_upgrade_decision('close/noallocation', 'confirmation')


  def test_alarm_compute_node_create_upgrade_decision_never(self):
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('open/public', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('open/personal', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('open/subscription', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('close/outdated', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('close/maintanance', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('close/termination', 'never')
    self._test_alarm_compute_node_create_upgrade_decision_not_visited('close/noallocation', 'never')

  def test_alarm_instance_tree_create_upgrade_decision(self):
    instance_tree = self._makeInstanceTree()
    self._test_alarm(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision')

  def test_alarm_create_upgrade_decision_destroyed_instance_tree(self):
    instance_tree = self._makeInstanceTree(slap_state="destroy_requested")
    self._test_alarm_not_visited(
      self.portal.portal_alarms.slapos_pdm_instance_tree_create_upgrade_decision,
      instance_tree,
      'InstanceTree_createUpgradeDecision')
