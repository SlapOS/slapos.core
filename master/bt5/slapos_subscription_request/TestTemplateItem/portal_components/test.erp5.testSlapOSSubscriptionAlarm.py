# -*- coding:utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Nexedi SA and Contributors. All Rights Reserved.
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixin

class TestSlapOSSubscriptionRequestProcessAlarm(SlapOSTestCaseMixin):

  #################################################################
  # slapos_subscription_request_create_from_orphaned_item
  #################################################################
  def _test_alarm_slapos_subscription_request_create_from_orphaned_item(self, portal_type):
    script_name = "Item_createSubscriptionRequest"
    alarm = self.portal.portal_alarms.slapos_subscription_request_create_from_orphaned_item

    #####################################################
    # Instance Tree without Subscription Request
    document = self.portal.getDefaultModule(portal_type).newContent(
        portal_type=portal_type,
        title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    self._test_alarm(alarm, document, script_name)

    #####################################################
    # Instance Tree with Subscription Request
    document = self.portal.getDefaultModule(portal_type).newContent(
        portal_type=portal_type,
        title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request',
        title="Test Subscription Request %s" % self.new_id,
        aggregate_value=document
    )
    self.tic()
    self._test_alarm_not_visited(alarm, document, script_name)
    #####################################################
    # Instance Tree aggregated to another portal type
    document = self.portal.getDefaultModule(portal_type).newContent(
        portal_type=portal_type,
        title="Test %s another portal type %s" % (portal_type, self.new_id)
    )
    document.validate()
    self.tic()
    self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List',
        title="Test Sale Packing List %s" % self.new_id,
    ).newContent(
      portal_type="Sale Packing List Line",
      aggregate_value=document
    )
    self.tic()
    self._test_alarm(alarm, document, script_name)

  def test_Item_createSubscriptionRequest_alarm_fromOrphanedInstanceTree(self):
    self._test_alarm_slapos_subscription_request_create_from_orphaned_item("Instance Tree")

  def test_Item_createSubscriptionRequest_alarm_fromOrphanedComputeNode(self):
    self._test_alarm_slapos_subscription_request_create_from_orphaned_item("Compute Node")

  def test_Item_createSubscriptionRequest_alarm_fromOrphanedProject(self):
    portal_type = 'Project'
    script_name = "Item_createSubscriptionRequest"
    alarm = self.portal.portal_alarms.slapos_subscription_request_create_from_orphaned_item
    document = self.portal.getDefaultModule(portal_type).newContent(
        portal_type=portal_type,
        title="Test %s no subscription %s" % (portal_type, self.new_id)
    )
    self._test_alarm_not_visited(alarm, document, script_name)


class TestSlapOSSubscriptionRequestValidateAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_subscription_request_validate_submitted
  #################################################################
  def _createSubscriptionRequest(self):
    return self.portal.subscription_request_module.newContent(
      portal_type='Subscription Request',
      title="Test subscription %s" % (self.generateNewId())
    )

  def test_SubscriptionRequest_validateIfSubmitted_alarm_notSubmitted(self):
    script_name = "SubscriptionRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_request_validate_submitted
    self._test_alarm_not_visited(alarm, self._createSubscriptionRequest(), script_name)

  def test_SubscriptionRequest_validateIfSubmitted_alarm_submitted(self):
    script_name = "SubscriptionRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_request_validate_submitted
    subscription_request = self._createSubscriptionRequest()
    self.portal.portal_workflow._jumpToStateFor(subscription_request, 'submitted')
    self._test_alarm(alarm, subscription_request, script_name)

class TestSlapOSSubscriptionRequestCancelAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_subscription_request_cancel_submitted
  #################################################################
  def _createSubscriptionRequest(self):
    return self.portal.subscription_request_module.newContent(
      portal_type='Subscription Request',
      title="Test subscription %s" % (self.generateNewId())
    )

  def test_SubscriptionRequest_validateIfSubmitted_alarm_notSubmitted(self):
    script_name = "SubscriptionRequest_cancelIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_request_cancel_submitted
    self._test_alarm_not_visited(alarm, self._createSubscriptionRequest(), script_name)

  def test_SubscriptionRequest_cancelIfSubmitted_alarm_submitted(self):
    script_name = "SubscriptionRequest_cancelIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_request_cancel_submitted
    subscription_request = self._createSubscriptionRequest()
    self.portal.portal_workflow._jumpToStateFor(subscription_request, 'submitted')
    self._test_alarm(alarm, subscription_request, script_name)


class TestSlapOSSubscriptionChangeRequestValidateAlarm(SlapOSTestCaseMixin):
  #################################################################
  # slapos_subscription_change_request_validate_submitted
  #################################################################
  def _createSubscriptionChangeRequest(self):
    return self.portal.subscription_change_request_module.newContent(
      portal_type='Subscription Change Request',
      title="Test subscription change %s" % (self.generateNewId())
    )

  def test_SubscriptionChangeRequest_validateIfSubmitted_alarm_notSubmitted(self):
    script_name = "SubscriptionChangeRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_validate_submitted
    self._test_alarm_not_visited(alarm, self._createSubscriptionChangeRequest(), script_name)

  def test_SubscriptionChangeRequest_validateIfSubmitted_alarm_submitted(self):
    script_name = "SubscriptionChangeRequest_validateIfSubmitted"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_validate_submitted
    subscription_request = self._createSubscriptionChangeRequest()
    self.portal.portal_workflow._jumpToStateFor(subscription_request, 'submitted')
    self._test_alarm(alarm, subscription_request, script_name)
