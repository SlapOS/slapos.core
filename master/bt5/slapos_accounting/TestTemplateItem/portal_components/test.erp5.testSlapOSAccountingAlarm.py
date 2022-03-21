# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
       
import transaction
import time
from functools import wraps
from Products.ERP5Type.tests.utils import createZODBPythonScript
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin, withAbort

import os
import tempfile
from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate#, getClosestDate
from zExceptions import Unauthorized

AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL = 'sale_trade_condition_module/slapos_aggregated_trade_condition_v3'

class Simulator:
  def __init__(self, outfile, method, to_return=None):
    self.outfile = outfile
    open(self.outfile, 'w').write(repr([]))
    self.method = method
    self.to_return = to_return

  def __call__(self, *args, **kwargs):
    """Simulation Method"""
    old = open(self.outfile, 'r').read()
    if old:
      l = eval(old) #pylint: disable=eval-used
    else:
      l = []
    l.append({'recmethod': self.method,
      'recargs': args,
      'reckwargs': kwargs})
    open(self.outfile, 'w').write(repr(l))
    return self.to_return

def simulateByEditWorkflowMark(script_name):
  def wrapper(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
      if script_name in self.portal.portal_skins.custom.objectIds():
        raise ValueError('Precondition failed: %s exists in custom' % script_name)
      createZODBPythonScript(self.portal.portal_skins.custom,
                          script_name,
                          '*args, **kwargs',
                          '# Script body\n'
  """context.portal_workflow.doActionFor(context, action='edit_action', comment='Visited by %s') """ % script_name )
      transaction.commit()
      try:
        result = func(self, *args, **kwargs)
      finally:
        if script_name in self.portal.portal_skins.custom.objectIds():
          self.portal.portal_skins.custom.manage_delObjects(script_name)
        transaction.commit()
      return result
    return wrapped
  return wrapper

def simulateByTitlewMark(script_name):
  def wrapper(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
      if script_name in self.portal.portal_skins.custom.objectIds():
        raise ValueError('Precondition failed: %s exists in custom' % script_name)
      createZODBPythonScript(self.portal.portal_skins.custom,
                          script_name,
                          '*args, **kwargs',
                          '# Script body\n'
"""
if context.getTitle() == 'Not visited by %s':
  context.setTitle('Visited by %s')
""" %(script_name, script_name))
      transaction.commit()
      try:
        result = func(self, *args, **kwargs)
      finally:
        if script_name in self.portal.portal_skins.custom.objectIds():
          self.portal.portal_skins.custom.manage_delObjects(script_name)
        transaction.commit()
      return result
    return wrapped
  return wrapper

class TestOpenSaleOrderAlarm(SlapOSTestCaseMixin):
  def test_noOSO_newPerson(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()

    self.assertEqual(None, self.portal.portal_catalog.getResultValue(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    ))

  def test_noOSO_after_fixConsistency(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    person.fixConsistency()
    self.tic()

    self.assertEqual(None, self.portal.portal_catalog.getResultValue(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    ))

  @simulateByEditWorkflowMark('InstanceTree_requestUpdateOpenSaleOrder')
  def test_alarm_HS_diverged(self):
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId())
    self.tic()

    self.portal.portal_alarms\
        .slapos_request_update_instance_tree_open_sale_order\
        .activeSense()
    self.tic()
    self.assertEqual(
        'Visited by InstanceTree_requestUpdateOpenSaleOrder',
        subscription.workflow_history['edit_workflow'][-1]['comment'])

class TestInstanceTree_requestUpdateOpenSaleOrder(SlapOSTestCaseMixin):
  def test_REQUEST_disallowed(self):
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    self.assertRaises(
      Unauthorized,
      subscription.InstanceTree_requestUpdateOpenSaleOrder,
      "sale_trade_condition_module/default_subscription_trade_condition",
      REQUEST={})

  def test_solved_InstanceTree(self):
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    self.portal.portal_workflow._jumpToStateFor(subscription, 'solved')
    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.assertEqual(subscription.getCausalityState(), 'solved')

  def test_empty_InstanceTree(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(
      specialise="sale_trade_condition_module/default_subscription_trade_condition"
    )
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(1,len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    sale_trade_condition = open_sale_order.getSpecialiseValue()
    self.assertEqual(
      "sale_trade_condition_module/default_subscription_trade_condition",
      sale_trade_condition.getRelativeUrl()
    )
    sale_supply_line = sale_trade_condition.contentValues(portql_type="Sale Supply Line")[0]

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    hosting_subscription = line.getAggregateValueList()[0]
    self.assertEqual("Hosting Subscription",
                     hosting_subscription.getPortalType())
    self.assertEqual("validated",
                     hosting_subscription.getValidationState())
    self.assertEqual(subscription.getRelativeUrl(), line.getAggregateList()[1])
    self.assertEqual(sale_supply_line.getResource(),
        line.getResource())
    service = line.getResourceValue()
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(service.getQuantityUnit(),
        line.getQuantityUnit())
    self.assertEqual(service.getUse(),
        line.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        line.getBaseContributionList())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())
    self.assertEqual(DateTime().earliestTime(), line.getStartDate())
    self.assertEqual(min(DateTime().day(), 28),
                     hosting_subscription.getPeriodicityMonthDay())
    start_date = addToDate(line.getStartDate(), to_add={'month': 1})
    start_date = addToDate(start_date, to_add={'second': -1})
    while start_date.day() >= 28:
      start_date = addToDate(start_date, to_add={'day': -1})
    self.assertEqual(start_date, line.getStopDate())

  def test_usualLifetime_InstanceTree(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'] = [{
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    }]
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(
      specialise="sale_trade_condition_module/default_subscription_trade_condition"
    )
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    sale_trade_condition = open_sale_order.getSpecialiseValue()
    self.assertEqual(
      "sale_trade_condition_module/default_subscription_trade_condition",
      sale_trade_condition.getRelativeUrl()
    )
    sale_supply_line = sale_trade_condition.contentValues(portql_type="Sale Supply Line")[0]

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    hosting_subscription = line.getAggregateValueList()[0]
    # self.assertEqual(hosting_subscription.getPeriodicityMonthDay(), 1)
    self.assertEqual("Hosting Subscription",
                     hosting_subscription.getPortalType())
    self.assertEqual("validated",
                     hosting_subscription.getValidationState())
    self.assertEqual(subscription.getRelativeUrl(), line.getAggregateList()[1])
    self.assertEqual(sale_supply_line.getResource(),
        line.getResource())
    service = line.getResourceValue()
    self.assertEqual(service.getQuantityUnit(),
        line.getQuantityUnit())
    self.assertEqual(service.getUse(),
        line.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        line.getBaseContributionList())
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())
    self.assertEqual(DateTime().earliestTime(), line.getStartDate())
    self.assertEqual(min(DateTime().day(), 28),
                     hosting_subscription.getPeriodicityMonthDay())
    start_date = addToDate(line.getStartDate(), to_add={'month': 1})
    start_date = addToDate(start_date, to_add={'second': -1})
    while start_date.day() >= 28:
      start_date = addToDate(start_date, to_add={'day': -1})
    self.assertEqual(start_date, line.getStopDate())

    destroy_time = DateTime('2112/02/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_time,
        'action': 'request_destroy'
    })
    subscription.diverge()
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(
      specialise="sale_trade_condition_module/default_subscription_trade_condition"
    )
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    validated_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'validated']
    archived_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'archived']

    self.assertEqual(0, len(validated_open_sale_order_list))
    self.assertEqual(1, len(archived_open_sale_order_list))
    
    archived_open_sale_order = archived_open_sale_order_list[0]\
        .getObject()
    self.assertEqual(open_sale_order.getRelativeUrl(),
        archived_open_sale_order.getRelativeUrl())

    archived_line_list = archived_open_sale_order.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(1, len(archived_line_list))

    archived_line = archived_line_list[0].getObject()

    self.assertEqual(line.getRelativeUrl(), archived_line.getRelativeUrl())

    self.assertEqual(subscription.getRelativeUrl(),
        archived_line.getAggregateList()[1])
    self.assertEqual(sale_supply_line.getResource(),
        archived_line.getResource())
    self.assertEqual(service.getQuantityUnit(),
        archived_line.getQuantityUnit())
    self.assertEqual(service.getUse(),
        archived_line.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        archived_line.getBaseContributionList())
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())
    self.assertEqual(DateTime().earliestTime(), archived_line.getStartDate())
    self.assertEqual(DateTime('2112/02/02'), line.getStopDate())

  def test_lateAnalysed_InstanceTree(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    subscription.workflow_history['instance_slap_interface_workflow'] = []
    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    })

    destroy_time = DateTime('2012/02/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'destroy_requested',
        'time': destroy_time,
        'action': 'request_destroy'
    })
    subscription.edit(periodicity_month_day_list=[])
    subscription.fixConsistency()
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(0, len(open_sale_order_list))

  def test_two_InstanceTree(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')

    request_time = DateTime('2012/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'] = [{
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    }]
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    sale_trade_condition = open_sale_order.getSpecialiseValue()
    self.assertEqual(
      "sale_trade_condition_module/default_subscription_trade_condition",
      sale_trade_condition.getRelativeUrl()
    )
    sale_supply_line = sale_trade_condition.contentValues(portql_type="Sale Supply Line")[0]

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()

    self.assertEqual("Hosting Subscription",
                     line.getAggregateValueList()[0].getPortalType())
    self.assertEqual("validated",
                     line.getAggregateValueList()[0].getValidationState())
    self.assertEqual(subscription.getRelativeUrl(), line.getAggregateList()[1])
    self.assertEqual(sale_supply_line.getResource(),
        line.getResource())
    service = line.getResourceValue()
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(service.getQuantityUnit(),
        line.getQuantityUnit())
    self.assertEqual(service.getUse(),
        line.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        line.getBaseContributionList())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())

    subscription2 = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription2.edit(reference='TESTHS-%s' % self.generateNewId(),
        title='Test Title %s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription2, 'validated')

    request_time_2 = DateTime('2012/08/01')
    subscription2.workflow_history['instance_slap_interface_workflow'] = [{
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time_2,
        'action': 'request_instance'
    }]
    subscription2.edit(periodicity_month_day_list=[])
    subscription2.fixConsistency()
    self.tic()

    subscription2.InstanceTree_requestUpdateOpenSaleOrder(
      specialise="sale_trade_condition_module/default_subscription_trade_condition"
    )
    self.tic()

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(2, len(open_sale_order_list))
    validated_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'validated']
    archived_open_sale_order_list = [q for q in open_sale_order_list
        if q.getValidationState() == 'archived']
    self.assertEqual(2, len(validated_open_sale_order_list))
    self.assertEqual(0, len(archived_open_sale_order_list))


    open_sale_order_2 = [x for x in validated_open_sale_order_list if x.getRelativeUrl() != open_sale_order.getRelativeUrl()][0]
    self.assertEqual(open_sale_order.getRelativeUrl(), [x for x in validated_open_sale_order_list if x.getRelativeUrl() == open_sale_order.getRelativeUrl()][0].getRelativeUrl())

    sale_trade_condition2 = open_sale_order.getSpecialiseValue()
    self.assertEqual(
      "sale_trade_condition_module/default_subscription_trade_condition",
      sale_trade_condition2.getRelativeUrl()
    )

    validated_line_list = open_sale_order_2.contentValues(
        portal_type='Open Sale Order Line')
    self.assertEqual(1, len(validated_line_list))
    validated_line_2 = validated_line_list[0]
    validated_line_1 = line

    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())

    hosting_subscription_2 = validated_line_2.getAggregateValueList()[0]
    self.assertEqual("Hosting Subscription",
                     hosting_subscription_2.getPortalType())
    self.assertEqual("validated",
                     hosting_subscription_2.getValidationState())
    self.assertEqual(subscription2.getRelativeUrl(), validated_line_2.getAggregateList()[1])

    self.assertEqual(service.getQuantityUnit(),
        validated_line_1.getQuantityUnit())
    self.assertEqual(service.getUse(),
        validated_line_1.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        validated_line_1.getBaseContributionList())
    self.assertEqual(sale_supply_line.getResource(),
        validated_line_1.getResource())
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())
    #self.assertEqual(request_time, validated_line_1.getStartDate())
    #self.assertEqual(stop_date, validated_line_1.getStopDate())

    self.assertEqual(service.getQuantityUnit(),
        validated_line_2.getQuantityUnit())
    self.assertEqual(service.getUse(),
        validated_line_2.getUse())
    self.assertSameSet(service.getBaseContributionList(),
        validated_line_2.getBaseContributionList())
    self.assertEqual(sale_supply_line.getResource(),
        validated_line_2.getResource())
    self.assertEqual(1,
        line.getQuantity())
    self.assertEqual(sale_supply_line.getBasePrice(),
        line.getPrice())
    #self.assertEqual(request_time_2, validated_line_2.getStartDate())
    #self.assertEqual(stop_date_2, validated_line_2.getStopDate())

  def test_instance_tree_start_date_not_changed(self):
    # if there was no request_instance the getCreationDate has been used
    # but if request_instance appeared start_date is not changed
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()

    request_time = DateTime('2112/01/01')
    subscription.workflow_history['instance_slap_interface_workflow'].append({
        'comment':'Simulated request instance',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'start_requested',
        'time': request_time,
        'action': 'request_instance'
    })
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(1, len(open_sale_order_list))
    open_sale_order = open_sale_order_list[0].getObject()
    self.assertEqual('validated', open_sale_order.getValidationState())

    open_sale_order_line_list = open_sale_order.contentValues(
        portal_type='Open Sale Order Line')

    self.assertEqual(1, len(open_sale_order_line_list))
    line = open_sale_order_line_list[0].getObject()
    self.assertEqual(subscription.getCreationDate().earliestTime(),
                     line.getStartDate())

  def test_instance_tree_diverged_to_solve(self):
    # check that HS becomes solved even if not modification is needed on open
    # order
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.assertEqual(subscription.getCausalityState(), 'diverged')
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    self.portal.portal_workflow._jumpToStateFor(subscription, 'diverged')
    subscription.reindexObject()
    self.assertEqual(subscription.getCausalityState(), 'diverged')
    self.assertEqual(subscription.getSlapState(), 'draft')
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

  def test_empty_destroyed_InstanceTree(self):
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    self.tic()
    subscription = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    subscription.edit(reference='TESTHS-%s' % self.generateNewId(),
        destination_section=person.getRelativeUrl())
    self.portal.portal_workflow._jumpToStateFor(subscription, 'validated')
    self.portal.portal_workflow._jumpToStateFor(subscription, 'destroy_requested')
    self.tic()

    subscription.InstanceTree_requestUpdateOpenSaleOrder(specialise="sale_trade_condition_module/default_subscription_trade_condition")
    self.tic()
    self.assertEqual(subscription.getCausalityState(), 'solved')

    open_sale_order_list = self.portal.portal_catalog(
        portal_type='Open Sale Order',
        default_destination_uid=person.getUid()
    )

    self.assertEqual(0,len(open_sale_order_list))


class TestSlapOSTriggerBuildAlarm(SlapOSTestCaseMixin):
  @simulateByTitlewMark('SimulationMovement_buildSlapOS')
  def test_SimulationMovement_withoutDelivery(self):
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        title='Not visited by SimulationMovement_buildSlapOS')
    self.tic()

    self.portal.portal_alarms.slapos_trigger_build.activeSense()
    self.tic()

    self.assertEqual(
        'Visited by SimulationMovement_buildSlapOS',
        simulation_movement.getTitle())

  @simulateByTitlewMark('SimulationMovement_buildSlapOS')
  def test_SimulationMovement_withDelivery(self):
    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = applied_rule.newContent(
        portal_type='Simulation Movement',
        delivery=delivery_line.getRelativeUrl(),
        title='Shall be visited by SimulationMovement_buildSlapOS')
    self.tic()

    self.portal.portal_alarms.slapos_trigger_build.activeSense()
    self.tic()

    self.assertNotEqual(
        'Not visited by SimulationMovement_buildSlapOS',
        simulation_movement.getTitle())

  @withAbort
  def test_SimulationMovement_buildSlapOS(self):
    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]

    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality=root_business_link.getRelativeUrl(),
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality=business_link.getRelativeUrl(),
        portal_type='Simulation Movement')

    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from erp5.component.document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {'path': '%s/%%' % root_applied_rule.getPath(),
        'activate_kw': {'tag': 'root_tag'}}}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            root_business_link.getUid(), root_applied_rule.getUid()),
          'after_tag': 'root_tag', 'activity': 'SQLQueue'}}],
        activate_value)

      open(build_simulator, 'w').truncate()
      open(activate_simulator, 'w').truncate()

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([{
        'recmethod': 'build',
        'recargs': (),
        'reckwargs': {'path': '%s/%%' % root_applied_rule.getPath(),
        'activate_kw': {'tag': 'lower_tag'}}}],
        build_value
      )
      self.assertEqual([{
        'recmethod': 'activate',
        'recargs': (),
        'reckwargs': {'tag': 'build_in_progress_%s_%s' % (
            business_link.getUid(), root_applied_rule.getUid()),
          'after_tag': 'lower_tag', 'activity': 'SQLQueue'}}],
        activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)

  @withAbort
  def test_SimulationMovement_buildSlapOS_withDelivery(self):
    build_simulator = tempfile.mkstemp()[1]
    activate_simulator = tempfile.mkstemp()[1]

    delivery = self.portal.sale_packing_list_module.newContent(
        portal_type='Sale Packing List')
    delivery_line = delivery.newContent(portal_type='Sale Packing List Line')
    business_process = self.portal.business_process_module.newContent(
        portal_type='Business Process')
    root_business_link = business_process.newContent(
        portal_type='Business Link')
    business_link = business_process.newContent(portal_type='Business Link')

    root_applied_rule = self.portal.portal_simulation.newContent(
        portal_type='Applied Rule')
    simulation_movement = root_applied_rule.newContent(
        causality=root_business_link.getRelativeUrl(),
        delivery=delivery_line.getRelativeUrl(),
        portal_type='Simulation Movement')

    applied_rule = simulation_movement.newContent(portal_type='Applied Rule')
    lower_simulation_movement = applied_rule.newContent(
        causality=business_link.getRelativeUrl(),
        delivery=delivery_line.getRelativeUrl(),
        portal_type='Simulation Movement')

    try:
      from Products.CMFActivity.ActiveObject import ActiveObject
      ActiveObject.original_activate = ActiveObject.activate
      ActiveObject.activate = Simulator(activate_simulator, 'activate',
          root_applied_rule)
      from erp5.component.document.BusinessLink import BusinessLink
      BusinessLink.original_build = BusinessLink.build
      BusinessLink.build = Simulator(build_simulator, 'build')

      simulation_movement.SimulationMovement_buildSlapOS(tag='root_tag')

      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

      open(build_simulator, 'w').write(repr([]))
      open(activate_simulator, 'w').write(repr([]))

      lower_simulation_movement.SimulationMovement_buildSlapOS(tag='lower_tag')
      build_value = eval(open(build_simulator).read()) #pylint: disable=eval-used
      activate_value = eval(open(activate_simulator).read()) #pylint: disable=eval-used

      self.assertEqual([], build_value)
      self.assertEqual([], activate_value)

    finally:
      ActiveObject.activate = ActiveObject.original_activate
      delattr(ActiveObject, 'original_activate')
      BusinessLink.build = BusinessLink.original_build
      delattr(BusinessLink, 'original_build')
      if os.path.exists(build_simulator):
        os.unlink(build_simulator)
      if os.path.exists(activate_simulator):
        os.unlink(activate_simulator)

class TestSlapOSManageBuildingCalculatingDeliveryAlarm(SlapOSTestCaseMixin):
  @simulateByTitlewMark('Delivery_manageBuildingCalculatingDelivery')
  def _test(self, state, message):
    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type='Sale Packing List')
    self.portal.portal_workflow._jumpToStateFor(delivery, state)
    self.tic()

    self.portal.portal_alarms.slapos_manage_building_calculating_delivery\
        .activeSense()
    self.tic()

    self.assertEqual(message, delivery.getTitle())

  def test_building(self):
    self._test('building', 'Visited by Delivery_manageBuildingCalculatingDelivery')

  def test_calculating(self):
    self._test('calculating', 'Visited by Delivery_manageBuildingCalculatingDelivery')

  def test_diverged(self):
    self._test('diverged', 'Not visited by Delivery_manageBuildingCalculatingDelivery')

  def test_solved(self):
    self._test('solved', 'Not visited by Delivery_manageBuildingCalculatingDelivery')

  @withAbort
  def _test_Delivery_manageBuildingCalculatingDelivery(self, state, empty=False):
    updateCausalityState_simulator = tempfile.mkstemp()[1]
    updateSimulation_simulator = tempfile.mkstemp()[1]

    delivery = self.portal.sale_packing_list_module.newContent(
        title='Not visited by Delivery_manageBuildingCalculatingDelivery',
        portal_type='Sale Packing List')
    self.portal.portal_workflow._jumpToStateFor(delivery, state)

    try:
      from erp5.component.document.Delivery import Delivery
      Delivery.original_updateCausalityState = Delivery.updateCausalityState
      Delivery.original_updateSimulation = Delivery.updateSimulation
      Delivery.updateCausalityState = Simulator(
          updateCausalityState_simulator, 'updateCausalityState')
      Delivery.updateSimulation = Simulator(
          updateSimulation_simulator, 'updateSimulation')

      delivery.Delivery_manageBuildingCalculatingDelivery()

      updateCausalityState_value = eval(open(updateCausalityState_simulator).read()) #pylint: disable=eval-used
      updateSimulation_value = eval(open(updateSimulation_simulator).read()) #pylint: disable=eval-used

      if empty:
        self.assertEqual([], updateCausalityState_value)
        self.assertEqual([], updateSimulation_value)
      else:
        self.assertEqual([{
          'recmethod': 'updateCausalityState',
          'recargs': (),
          'reckwargs': {'solve_automatically': True}}],
          updateCausalityState_value
        )
        self.assertEqual([{
          'recmethod': 'updateSimulation',
          'recargs': (),
          'reckwargs': {'expand_root': 1, 'expand_related': 1}}],
          updateSimulation_value
        )
    finally:
      Delivery.updateCausalityState = Delivery.original_updateCausalityState
      Delivery.updateSimulation = Delivery.original_updateSimulation
      delattr(Delivery, 'original_updateCausalityState')
      delattr(Delivery, 'original_updateSimulation')
      if os.path.exists(updateCausalityState_simulator):
        os.unlink(updateCausalityState_simulator)
      if os.path.exists(updateSimulation_simulator):
        os.unlink(updateSimulation_simulator)

  def test_Delivery_manageBuildingCalculatingDelivery_calculating(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('calculating')

  def test_Delivery_manageBuildingCalculatingDelivery_building(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('building')

  def test_Delivery_manageBuildingCalculatingDelivery_solved(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('solved', True)

  def test_Delivery_manageBuildingCalculatingDelivery_diverged(self):
    self._test_Delivery_manageBuildingCalculatingDelivery('diverged', True)

class TestSlapOSConfirmedDeliveryMixin:
  def _test(self, simulation_state, causality_state, specialise, positive,
      delivery_date=DateTime('2012/04/22'),
      accounting_date=DateTime('2012/04/28')):
    @simulateByTitlewMark(self.script)
    def _real(self, simulation_state, causality_state, specialise, positive,
          delivery_date,
          accounting_date):
      not_visited = 'Not visited by %s' % self.script
      visited = 'Visited by %s' % self.script
      module = self.portal.getDefaultModule(portal_type=self.portal_type)
      delivery = module.newContent(title=not_visited, start_date=delivery_date,
          portal_type=self.portal_type, specialise=specialise)
      _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
      _jumpToStateFor(delivery, simulation_state)
      _jumpToStateFor(delivery, causality_state)
      self.tic()

      alarm = getattr(self.portal.portal_alarms, self.alarm)
      alarm.activeSense(params=dict(accounting_date=accounting_date))
      self.tic()

      if positive:
        self.assertEqual(visited, delivery.getTitle())
      else:
        self.assertEqual(not_visited, delivery.getTitle())
    _real(self, simulation_state, causality_state, specialise, positive,
        delivery_date, accounting_date)

  def test_typical(self):
    self._test('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, True)

  def test_bad_specialise(self):
    self._test('confirmed', 'solved', None, False)

  def test_bad_simulation_state(self):
    self._test('started', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, False)

  def test_bad_causality_state(self):
    self._test('confirmed', 'calculating',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, False)

  @withAbort
  def _test_script(self, simulation_state, causality_state, specialise,
        destination_state, consistency_failure=False):
    module = self.portal.getDefaultModule(portal_type=self.portal_type)
    delivery = module.newContent(portal_type=self.portal_type,
        specialise=specialise, start_date=DateTime())
    _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
    _jumpToStateFor(delivery, simulation_state)
    _jumpToStateFor(delivery, causality_state)
    def checkConsistency(*args, **kwargs):
      if consistency_failure:
        return ['bad']
      else:
        return []
    try:
      from Products.ERP5Type.Core.Folder import Folder
      Folder.original_checkConsistency = Folder.checkConsistency
      Folder.checkConsistency = checkConsistency
      getattr(delivery, self.script)()
    finally:
      Folder.checkConsistency = Folder.original_checkConsistency
      delattr(Folder, 'original_checkConsistency')
    self.assertEqual(destination_state, delivery.getSimulationState())

  def test_script_typical(self):
    self._test_script('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        self.destination_state)

  def test_script_bad_specialise(self):
    self._test_script('confirmed', 'solved', None, 'confirmed')

  def test_script_bad_simulation_state(self):
    self._test_script('started', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'started')

  def test_script_bad_causality_state(self):
    self._test_script('confirmed', 'building',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'confirmed')

  def test_script_bad_consistency(self):
    self._test_script('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'confirmed', True)

class TestSlapOSStartConfirmedAggregatedSalePackingListAlarm(
      SlapOSTestCaseMixin, TestSlapOSConfirmedDeliveryMixin):
  destination_state = 'started'
  script = 'Delivery_startConfirmedAggregatedSalePackingList'
  portal_type = 'Sale Packing List'
  alarm = 'slapos_start_confirmed_aggregated_sale_packing_list'

  def test_previous_month(self):
    self._test('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        True, delivery_date=DateTime("2012/03/22"),
        accounting_date=DateTime('2012/04/28'))

  def test_next_month(self):
    self._test('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        False, delivery_date=DateTime("2012/05/22"),
        accounting_date=DateTime('2012/04/28'))

  def test_same_month_early(self):
    self._test('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        False, delivery_date=DateTime("2012/04/22"),
        accounting_date=DateTime('2012/04/23'))

  def test_start_date_isnt_resetted(self):
    delivery = self.portal.sale_packing_list_module.newContent(
      portal_type="Sale Packing List",
      start_date=DateTime("2012/04/22"),
      specialise=AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
      source=self.expected_slapos_organisation,
      source_section=self.expected_slapos_organisation,
      destination=self.expected_slapos_organisation,
      destination_section=self.expected_slapos_organisation,
      destination_decision=self.expected_slapos_organisation,
      price_currency='currency_module/EUR',
      )
    delivery.newContent(
      portal_type="Sale Packing List Line",
      resource='service_module/slapos_instance_setup',
      quantity=0,
      price=0,
      )
    self.portal.portal_workflow._jumpToStateFor(delivery, 'solved')
    self.portal.portal_workflow._jumpToStateFor(delivery, 'confirmed')
    delivery.Delivery_startConfirmedAggregatedSalePackingList()
    self.assertNotEqual(delivery.getStartDate(),
                      DateTime().earliestTime())
    self.assertNotEqual(delivery.getStopDate(),
                      DateTime().earliestTime())
    self.assertEqual(delivery.getSimulationState(), 'started')

class TestSlapOSDeliverStartedAggregatedSalePackingListAlarm(
      SlapOSTestCaseMixin):
  destination_state = 'delivered'
  script = 'Delivery_deliverStartedAggregatedSalePackingList'
  portal_type = 'Sale Packing List'
  alarm = 'slapos_deliver_started_aggregated_sale_packing_list'

  def _test(self, simulation_state, causality_state, specialise, positive,
      delivery_date=DateTime('2012/04/22'),
      accounting_date=DateTime('2012/04/28')):
    @simulateByTitlewMark(self.script)
    def _real(self, simulation_state, causality_state, specialise, positive,
          delivery_date,
          accounting_date):
      not_visited = 'Not visited by %s' % self.script
      visited = 'Visited by %s' % self.script
      module = self.portal.getDefaultModule(portal_type=self.portal_type)
      delivery = module.newContent(title=not_visited, start_date=delivery_date,
          portal_type=self.portal_type, specialise=specialise)
      _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
      _jumpToStateFor(delivery, simulation_state)
      _jumpToStateFor(delivery, causality_state)
      self.tic()

      alarm = getattr(self.portal.portal_alarms, self.alarm)
      alarm.activeSense(params=dict(accounting_date=accounting_date))
      self.tic()

      if positive:
        self.assertEqual(visited, delivery.getTitle())
      else:
        self.assertEqual(not_visited, delivery.getTitle())
    _real(self, simulation_state, causality_state, specialise, positive,
        delivery_date, accounting_date)

  def test_typical(self):
    self._test('started', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, True)

  def test_bad_specialise(self):
    self._test('started', 'solved', None, False)

  def test_bad_simulation_state(self):
    self._test('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, False)

  def test_bad_causality_state(self):
    self._test('started', 'calculating',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL, False)

  @withAbort
  def _test_script(self, simulation_state, causality_state, specialise,
        destination_state, consistency_failure=False):
    module = self.portal.getDefaultModule(portal_type=self.portal_type)
    delivery = module.newContent(portal_type=self.portal_type,
        specialise=specialise, start_date=DateTime())
    _jumpToStateFor = self.portal.portal_workflow._jumpToStateFor
    _jumpToStateFor(delivery, simulation_state)
    _jumpToStateFor(delivery, causality_state)
    def checkConsistency(*args, **kwargs):
      if consistency_failure:
        return ['bad']
      else:
        return []
    try:
      from Products.ERP5Type.Core.Folder import Folder
      Folder.original_checkConsistency = Folder.checkConsistency
      Folder.checkConsistency = checkConsistency
      getattr(delivery, self.script)()
    finally:
      Folder.checkConsistency = Folder.original_checkConsistency
      delattr(Folder, 'original_checkConsistency')
    self.assertEqual(destination_state, delivery.getSimulationState())

  def test_script_typical(self):
    self._test_script('started', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        self.destination_state)

  def test_script_bad_specialise(self):
    self._test_script('started', 'solved', None, 'started')

  def test_script_bad_simulation_state(self):
    self._test_script('confirmed', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'confirmed')

  def test_script_bad_causality_state(self):
    self._test_script('started', 'building',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'started')

  def test_script_bad_consistency(self):
    self._test_script('started', 'solved',
        AGGREGATE_SALE_TRADE_CONDITION_RELATIVE_URL,
        'started', True)

class TestSlapOSStopConfirmedAggregatedSaleInvoiceTransactionAlarm(
      SlapOSTestCaseMixin, TestSlapOSConfirmedDeliveryMixin):
  destination_state = 'stopped'
  script = 'Delivery_stopConfirmedAggregatedSaleInvoiceTransaction'
  portal_type = 'Sale Invoice Transaction'
  alarm = 'slapos_stop_confirmed_aggregated_sale_invoice_transaction'

class TestSlapOSUpdateOpenSaleOrderPeriod(SlapOSTestCaseMixin):

  def createOpenOrder(self):
    open_order = self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )
    open_order.order()
    open_order.validate()
    return open_order

  def test_updatePeriod_REQUEST_disallowed(self):
    self.assertRaises(
      Unauthorized,
      self.portal.OpenSaleOrder_updatePeriod,
      REQUEST={})

  def test_updatePeriod_no_person(self):
    open_order = self.createOpenOrder()
    open_order.OpenSaleOrder_updatePeriod()

  def test_updatePeriod_validated(self):
    open_order = self.createOpenOrder()
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    open_order.edit(
      destination_decision_value=person,
    )
    open_order.newContent(
      portal_type="Open Sale Order Line"
    )

    self.assertRaises(AssertionError, open_order.OpenSaleOrder_updatePeriod)

  def test_updatePeriod_invalidated(self):
    open_order = self.createOpenOrder()
    person = self.portal.person_module.template_member\
        .Base_createCloneDocument(batch_mode=1)
    open_order.edit(
      destination_decision_value=person,
    )
    open_order.invalidate()
    open_order.newContent(
      portal_type="Open Sale Order Line"
    )
    open_order.OpenSaleOrder_updatePeriod()

  def test_alarm(self):
    open_order = self.createOpenOrder()
    open_order.newContent(portal_type="Open Sale Order Line")
    self.tic()
    script_name = "OpenSaleOrder_updatePeriod"
    alarm = self.portal.portal_alarms.slapos_update_open_sale_order_period
    
    self._test_alarm(
      alarm, open_order, script_name)

  def test_alarm_invalidated(self):
    open_order = self.createOpenOrder()
    open_order.newContent(portal_type="Open Sale Order Line")
    open_order.invalidate()
    self.tic()
    script_name = "OpenSaleOrder_updatePeriod"
    alarm = self.portal.portal_alarms.slapos_update_open_sale_order_period
    
    self._test_alarm_not_visited(
      alarm, open_order, script_name)

  def test_alarm_no_line(self):
    open_order = self.createOpenOrder()
    self.tic()
    script_name = "OpenSaleOrder_updatePeriod"
    alarm = self.portal.portal_alarms.slapos_update_open_sale_order_period
    
    self._test_alarm_not_visited(
      alarm, open_order, script_name)

class TestSlapOSReindexOpenSaleOrder(SlapOSTestCaseMixin):

  def createOpenOrder(self):
    return self.portal.open_sale_order_module.newContent(
        portal_type="Open Sale Order",
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
    )

  def _simulateScript(self, script_name, fake_return="False"):
    if script_name in self.portal.portal_skins.custom.objectIds():
      raise ValueError('Precondition failed: %s exists in custom' % script_name)
    createZODBPythonScript(self.portal.portal_skins.custom,
                        script_name,
                        'uid=None,*args, **kwargs',
                        '# Script body\n'
"""portal_workflow = context.portal_workflow
document = context.portal_catalog.getResultValue(uid=uid)
portal_workflow.doActionFor(document, action='edit_action', comment='Visited by %s') """ % script_name )
    transaction.commit()

  def test_alarm(self):
    open_order = self.createOpenOrder()
    self.tic()
    # Jut wait a bit so the line has a different timestamp > 1 sec.
    time.sleep(1)
    open_order.newContent(portal_type="Open Sale Order Line")
    self.tic()
    script_name = "OpenSaleOrder_reindexIfIndexedBeforeLine"
    alarm = self.portal.portal_alarms.slapos_reindex_open_sale_order
    
    self._test_alarm(
      alarm, open_order, script_name)

  def test_alarm_no_line(self):
    open_order = self.createOpenOrder()
    self.tic()
    script_name = "OpenSaleOrder_reindexIfIndexedBeforeLine"
    alarm = self.portal.portal_alarms.slapos_reindex_open_sale_order
    
    self._test_alarm_not_visited(
      alarm, open_order, script_name)

class TestSlapOSGeneratePackingListFromTioXML(SlapOSTestCaseMixin):

  def createTioXMLFile(self):
    document = self.portal.consumption_document_module.newContent(
      title=self.generateNewId(),
      reference="TESTTIOCONS-%s" % self.generateNewId(),
    )
    return document

  def test_alarm(self):
    document = self.createTioXMLFile()
    document.submit()
    self.tic()

    script_name = "ComputerConsumptionTioXMLFile_solveInvoicingGeneration"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_packing_list_from_tioxml

    self._test_alarm(
      alarm, document, script_name)

  def test_alarm_not_submitted(self):
    document = self.createTioXMLFile()
    self.tic()
    
    script_name = "ComputerConsumptionTioXMLFile_solveInvoicingGeneration"
    alarm = self.portal.portal_alarms.slapos_accounting_generate_packing_list_from_tioxml

    self._test_alarm_not_visited(
      alarm, document, script_name)


class TestSlapOSCancelSaleTnvoiceTransactionPaiedPaymentListAlarm(SlapOSTestCaseMixin):

  def _test_payment_is_draft(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    self.tic()

    self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list.activeSense()
    self.tic()

    self.assertNotEqual(
        'Not visited by PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped',
        payment_transaction.getTitle())

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_draft_payzen(self):
    self._test_payment_is_draft(payment_mode="payzen")

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_draft_wechat(self):
    self._test_payment_is_draft(payment_mode="wechat")

  def _test_payment_is_stopped(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    payment_transaction.setStartDate(DateTime())
    payment_transaction.confirm()
    payment_transaction.start()
    payment_transaction.stop()
    self.tic()

    self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list.activeSense()
    self.tic()

    self.assertNotEqual(
        'Not visited by PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped',
        payment_transaction.getTitle())

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_stopped_payzen(self):
    self._test_payment_is_stopped(payment_mode="payzen")

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_stopped_wechat(self):
    self._test_payment_is_stopped(payment_mode="wechat")


  def _test_payment_is_started(self, payment_mode):
    new_id = self.generateNewId()
    payment_transaction = self.portal.accounting_module.newContent(
      portal_type='Payment Transaction',
      title="Transaction %s" % new_id,
      reference="TESTTRANS-%s" % new_id,
      payment_mode=payment_mode
      )
    payment_transaction.setStartDate(DateTime())
    payment_transaction.confirm()
    payment_transaction.start()
    self.tic()

    self.portal.portal_alarms.slapos_cancel_sale_invoice_transaction_paied_payment_list.activeSense()
    self.tic()

    self.assertNotEqual(
        'Visited by PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped',
        payment_transaction.getTitle())

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_started_payzen(self):
    self._test_payment_is_started(payment_mode="payzen")

  @simulateByTitlewMark('PaymentTransaction_cancelIfSaleInvoiceTransactionIsGrouped')
  def test_payment_is_started_wechat(self):
    self._test_payment_is_started(payment_mode="wechat")

