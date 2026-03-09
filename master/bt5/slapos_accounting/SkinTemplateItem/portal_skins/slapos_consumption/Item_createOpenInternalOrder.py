from erp5.component.module.DateUtils import getClosestDate, addToDate
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

item = context
portal = context.getPortalObject()

if len(item.checkConsistency()) != 0:
  # Prevent getting many activity errors
  return

def storeWorkflowComment(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(ob=document,
                                          name='comment', wf_id='edit_workflow')
  if last_workflow_item != comment:
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

# Search an existing related open consumption order
open_consumption_order_line = portal.portal_catalog.getResultValue(
  portal_type='Open Internal Order Line',
  aggregate__uid=item.getUid()
)
if open_consumption_order_line is not None:
  return

#################################################################
# Find matching Service
service = None

if item.getPortalType() in ['Software Instance', 'Slave Instance']:
  service = portal.restrictedTraverse('service_module/slapos_software_instance_subscription')
  project_value = item.getFollowUpValue(portal_type="Project")
elif item.getPortalType() == 'Compute Node':
  service = portal.restrictedTraverse('service_module/slapos_compute_node_subscription')
  project_value = item.getFollowUpValue(portal_type="Project")
else:
  raise ValueError('Unsupported portal type: %s (%s)' % (item.getPortalType(), item.getRelativeUrl()))

if service is None:
  storeWorkflowComment(item, 'Can not find a matching Service to generate the Subscription Request')
  return

#######################################################
# Search project open order
open_sale_order_movement_list = portal.portal_catalog(
  portal_type=['Open Sale Order Line'],
  aggregate__uid=project_value.getUid(),
  validation_state='validated',
  limit=1)

if len(open_sale_order_movement_list) == 0:
  # It is really unexpected that a report comes before the
  # Open order been created by the alarm, in case, this happens often
  # we can just skip (return), and retry later on.
  return storeWorkflowComment(item, "No open order for %s" % project_value.getRelativeUrl())

#######################################################
# Consumption Subscription
consumption_subscription = portal.consumption_subscription_module.newContent(
  portal_type="Consumption Subscription",
  # Put item reference in the title to simplify search
  title="subscription for %s" % item.getReference(),
  ledger_value=portal.portal_categories.ledger.automated,
)

edit_kw = {}
if consumption_subscription.getPeriodicityHour() is None:
  edit_kw['periodicity_hour_list'] = [0]
if consumption_subscription.getPeriodicityMinute() is None:
  edit_kw['periodicity_minute_list'] = [0]
if consumption_subscription.getPeriodicityMonthDay() is None:
  # do not use the same date for every users
  # to prevent overload of the server at this date
  # Use the item creation date for now, as this document is always accessible
  # without relying on portal_catalog / serialize
  start_date = getClosestDate(target_date=item.getCreationDate(), precision='day')
  while start_date.day() >= 29:
    start_date = addToDate(start_date, to_add={'day': -1})
  edit_kw['periodicity_month_day_list'] = [start_date.day()]
if edit_kw:
  consumption_subscription.edit(**edit_kw)

consumption_subscription.validate()

#######################################################
# Open Consumption Order
current_date = getClosestDate(target_date=consumption_subscription.getCreationDate(), precision='day')
next_period_date = consumption_subscription.getNextPeriodicalDate(current_date)

# if subscription_request.getQuantityUnit() == 'time/month':
# This start_date calculation ensures the first invoices period
# will be merged in the user monthly invoice
start_date = addToDate(next_period_date, to_add={'month': -1})
assert consumption_subscription.getNextPeriodicalDate(start_date) == next_period_date
#else:
#  raise ValueError('Unsupported quantity unit %s' % subscription_request.getQuantityUnit())

"""
source_value=subscription_request.getSourceValue(),
source_section_value=subscription_request.getSourceSectionValue(),
source_decision_value=subscription_request.getSourceDecisionValue(),
source_project_value=subscription_request.getSourceProjectValue(),
destination_value=subscription_request.getDestinationValue(),
destination_section_value=subscription_request.getDestinationSectionValue(),
destination_decision_value=subscription_request.getDestinationDecisionValue(),
destination_project_value=subscription_request.getDestinationProjectValue(),
"""
"""
causality_value=subscription_request,
price_currency_value=subscription_request.getPriceCurrencyValue(),
"""
open_sale_order_movement = open_sale_order_movement_list[0]
open_order_edit_kw = dict(
  title=consumption_subscription.getTitle(),
  start_date=start_date,

  # specialise_value=subscription_request.getSpecialiseValue(),
  # XXX XXX HARDCODED
  specialise='business_process_module/slapos_internal_subscription_business_process',
  destination_value=open_sale_order_movement.getSourceValue(),

  ledger_value=portal.portal_categories.ledger.automated,

  activate_kw=activate_kw
)

open_consumption_order = portal.open_internal_order_module.newContent(
  portal_type="Open Internal Order",

  # Do not set the stop_date, as we don't know
  # when the user will close the subscription
  stop_date=None,

  **open_order_edit_kw
)

open_order_line = open_consumption_order.newContent(
  portal_type="Open Internal Order Line",
  #resource_value=subscription_request.getResourceValue(),
  # XXX XXX HARDCODED
  resource_value=service,
  #quantity_unit_value=subscription_request.getQuantityUnitValue(),
  #base_contribution_list=subscription_request.getBaseContributionList(),
  #use=subscription_request.getUse(),
  activate_kw=activate_kw
)

open_order_line.edit(
  #quantity=subscription_request.getQuantity(),
  # XXX XXX hardcoded
  quantity=1,
  price=0,
  #price=subscription_request.getPrice(),
  aggregate_value_list=[
    consumption_subscription,
    item
  ],
  activate_kw=activate_kw
)

open_consumption_order.Delivery_fixBaseContributionTaxableRate()
open_consumption_order.Base_checkConsistency()
open_consumption_order.plan()
open_consumption_order.validate()

open_consumption_order.reindexObject(activate_kw=activate_kw)
item.reindexObject(activate_kw=activate_kw)

# Prevent concurrent transactions which could create the Open Consumption Order
item.serialize()

return open_consumption_order
