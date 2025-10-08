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
from DateTime import DateTime
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime


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


class TestSlaposSubscriptionGenerateSubscriptionChangeRequestForExpiredSaleTradeCondition(SlapOSTestCaseMixinWithAbort):

  def _createSaleTradeConditionToExpire(self):
    with TemporaryAlarmScript(self.portal, 'Base_reindexAndSenseAlarm',
                                             "'disabled'", attribute='comment'):
      sale_trade_condition_module = self.portal.sale_trade_condition_module
      ledger_automated = self.portal.portal_categories.ledger.automated

      specialised_sale_trade_condition_version1 = sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition',
        ledger_value=ledger_automated,
        title="Test specialised STC %s" % (self.generateNewId())
      )
      specialised_sale_trade_condition_version1.validate()

      # XXX Move to a script
      now = DateTime()
      container = specialised_sale_trade_condition_version1.getParentValue()
      clipboard = container.manage_copyObjects(ids=[specialised_sale_trade_condition_version1.getId()])
      specialised_sale_trade_condition_version2 = container[container.manage_pasteObjects(clipboard)[0]['new_id']]
      specialised_sale_trade_condition_version1.edit(
        expiration_date=now
      )
      specialised_sale_trade_condition_version2.edit(
        effective_date=now
      )
      specialised_sale_trade_condition_version2.validate()

      sale_trade_condition_to_expire = sale_trade_condition_module.newContent(
        portal_type='Sale Trade Condition',
        ledger_value=ledger_automated,
        title="Test STC to expire %s" % (self.generateNewId()),
        specialise_value=specialised_sale_trade_condition_version1
      )
      sale_trade_condition_to_expire.validate()
      self.tic()
    return sale_trade_condition_to_expire

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_alarm_notExpired(self):
    script_name = "SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_create_from_expired_sale_trade_condition
    self._test_alarm(alarm, self._createSaleTradeConditionToExpire(), script_name)

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_alarm_alreadyExpired(self):
    script_name = "SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_create_from_expired_sale_trade_condition
    sale_trade_condition = self._createSaleTradeConditionToExpire()
    sale_trade_condition.edit(expiration_date=DateTime())
    self.tic()
    self._test_alarm_not_visited(alarm, sale_trade_condition, script_name)

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_alarm_invalidated(self):
    script_name = "SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_create_from_expired_sale_trade_condition
    sale_trade_condition = self._createSaleTradeConditionToExpire()
    sale_trade_condition.invalidate()
    self.tic()
    self._test_alarm_not_visited(alarm, sale_trade_condition, script_name)

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_alarm_expiredInFutur(self):
    script_name = "SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition"
    alarm = self.portal.portal_alarms.slapos_subscription_change_request_create_from_expired_sale_trade_condition
    with PinnedDateTime(self, DateTime() + 1):
      sale_trade_condition = self._createSaleTradeConditionToExpire()
      self.tic()
    self._test_alarm_not_visited(alarm, sale_trade_condition, script_name)

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_script_notExpired(self):
    sale_trade_condition = self._createSaleTradeConditionToExpire()

    sale_trade_condition_change_request_relative_url = sale_trade_condition.SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition()
    self.assertEqual(sale_trade_condition.getValidationState(), "validated")
    self.assertEqual(sale_trade_condition.getExpirationDate(), None)

    sale_trade_condition_change_request = self.portal.restrictedTraverse(sale_trade_condition_change_request_relative_url)
    self.assertEqual(sale_trade_condition_change_request.getSimulationState(), "submitted")

    proposed_sale_trade_condition = sale_trade_condition_change_request.getSpecialiseValue()
    self.assertEqual(proposed_sale_trade_condition.getValidationState(), "draft")

    self.assertEqual(proposed_sale_trade_condition.getEffectiveDate(), None)
    self.assertEqual(proposed_sale_trade_condition.getTitle(), sale_trade_condition.getTitle())
    self.assertNotEqual(proposed_sale_trade_condition.getSpecialise(), sale_trade_condition.getSpecialise())
    # Check that the new specialised value was used
    old_specialise_value = sale_trade_condition.getSpecialiseValue()
    new_specialise_value = proposed_sale_trade_condition.getSpecialiseValue()
    self.assertEqual(new_specialise_value.getValidationState(), "validated")
    self.assertEqual(new_specialise_value.getEffectiveDate(), old_specialise_value.getExpirationDate())
    self.assertEqual(new_specialise_value.getTitle(), old_specialise_value.getTitle())

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_script_expired(self):
    sale_trade_condition = self._createSaleTradeConditionToExpire()
    now = DateTime()
    sale_trade_condition.edit(expiration_date=now)
    result = sale_trade_condition.SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition()

    self.assertEqual(sale_trade_condition.getValidationState(), "validated")
    self.assertEqual(sale_trade_condition.getExpirationDate(), now)
    self.assertEqual(result, None)

  def test_SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition_script_noNewVersionFound(self):
    sale_trade_condition = self._createSaleTradeConditionToExpire()
    new_version = self.portal.portal_catalog.getResultValue(
      portal_type='Sale Trade Condition',
      title={'query': sale_trade_condition.getSpecialiseTitle(), 'key': 'ExactMatch'},
      validation_state='validated',
      # The dates must match
      effective_date=sale_trade_condition.getSpecialiseValue().getExpirationDate(),
    )
    # Changing the date must be enough
    new_version.edit(effective_date=new_version.getEffectiveDate() - 1)
    self.tic()

    result = sale_trade_condition.SaleTradeCondition_generateNewVersionFromExpiredSaleTradeCondition()
    self.assertEqual(sale_trade_condition.getValidationState(), "validated")
    self.assertEqual(sale_trade_condition.getExpirationDate(), None)
    self.assertEqual(result, None)


