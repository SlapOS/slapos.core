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
  SlapOSTestCaseMixin, TemporaryAlarmScript, SlapOSTestCaseMixinWithAbort
import time

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


class TestSlaposCrmCheckStoppedEventFromSubscriptionRequestToDeliver(SlapOSTestCaseMixinWithAbort):

  event_portal_type = 'Web Message'

  def _createSubscriptionRequest(self):
    return self.portal.subscription_request_module.newContent(
      portal_type='Subscription Request',
      title="Test subscription %s" % (self.generateNewId())
    )

  def _makeEvent(self, follow_up_value):
    new_id = self.generateNewId()
    return self.portal.event_module.newContent(
      portal_type=self.event_portal_type,
      title='Test %s %s' % (self.event_portal_type, new_id),
      follow_up_value=follow_up_value
    )

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_alarm_stopped(self):
    subscription_request = self._createSubscriptionRequest()
    event = self._makeEvent(subscription_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_subscription_check_stopped_event_from_subscription_request_to_deliver
    self._test_alarm(alarm, event, "Event_checkStoppedFromSubscriptionRequestToDeliver")

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_alarm_delivered(self):
    subscription_request = self._createSubscriptionRequest()
    event = self._makeEvent(subscription_request)
    event.stop()
    event.deliver()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
       slapos_subscription_check_stopped_event_from_subscription_request_to_deliver
    self._test_alarm_not_visited(alarm, event,
      "Event_checkStoppedFromSubscriptionRequestToDeliver")

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_alarm_stoppedWithoutTicket(self):
    subscription_request = self._createSubscriptionRequest()
    event = self._makeEvent(subscription_request)
    event.setFollowUp(None)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    alarm = self.portal.portal_alarms.\
          slapos_subscription_check_stopped_event_from_subscription_request_to_deliver
    self._test_alarm_not_visited(alarm, event,
      "Event_checkStoppedFromSubscriptionRequestToDeliver")

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_script_invalidatedTicket(self):
    subscription_request = self._createSubscriptionRequest()
    subscription_request.validate()
    subscription_request.invalidate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(subscription_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")
    event.Event_checkStoppedFromSubscriptionRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "delivered")
    self.assertEqual(subscription_request.getSimulationState(), "invalidated")

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_script_validatedTicket(self):
    subscription_request = self._createSubscriptionRequest()
    subscription_request.validate()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(subscription_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(subscription_request.getSimulationState(), "validated")
    event.Event_checkStoppedFromSubscriptionRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(subscription_request.getSimulationState(), "validated")

  def test_Event_checkStoppedFromSubscriptionRequestToDeliver_script_suspendedTicket(self):
    subscription_request = self._createSubscriptionRequest()
    subscription_request.validate()
    subscription_request.suspend()
    self.tic()
    time.sleep(1)
    event = self._makeEvent(subscription_request)
    event.stop()
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      self.tic()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(subscription_request.getSimulationState(), "suspended")
    event.Event_checkStoppedFromSubscriptionRequestToDeliver()
    self.assertEqual(event.getSimulationState(), "stopped")
    self.assertEqual(subscription_request.getSimulationState(), "suspended")
