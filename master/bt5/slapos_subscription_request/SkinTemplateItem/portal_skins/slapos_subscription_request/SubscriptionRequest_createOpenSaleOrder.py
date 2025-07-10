from erp5.component.module.DateUtils import getClosestDate, addToDate

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
subscription_request = context

assert subscription_request.getAggregate('') != ''

activate_kw = None

#######################################################
# Hosting Subscription
hosting_subscription = portal.hosting_subscription_module.newContent(
  portal_type="Hosting Subscription",
  # Put item reference in the title to simplify search
  title="subscription for %s" % subscription_request.getAggregateValue().getReference(),
  ledger_value=portal.portal_categories.ledger.automated,
)


edit_kw = {}
if hosting_subscription.getPeriodicityHour() is None:
  edit_kw['periodicity_hour_list'] = [0]
if hosting_subscription.getPeriodicityMinute() is None:
  edit_kw['periodicity_minute_list'] = [0]
if hosting_subscription.getPeriodicityMonthDay() is None:
  # do not use the same date for every users
  # to prevent overload of the server at this date
  # Use the section creation date for now, as this document is always accessible
  # without relying on portal_catalog / serialize
  # Section is the entity which want to pay the monthly invoice
  section_entity = subscription_request.getDestinationSectionValue()
  start_date = getClosestDate(target_date=section_entity.getCreationDate(), precision='day')
  while start_date.day() >= 29:
    start_date = addToDate(start_date, to_add={'day': -1})
  edit_kw['periodicity_month_day_list'] = [start_date.day()]
if edit_kw:
  hosting_subscription.edit(**edit_kw)

hosting_subscription.validate()

#######################################################
# Open Sale Order

current_date = getClosestDate(target_date=hosting_subscription.getCreationDate(), precision='day')
next_period_date = hosting_subscription.getNextPeriodicalDate(current_date)

if subscription_request.getQuantityUnit() == 'time/month':
  # This start_date calculation ensures the first invoices period
  # will be merged in the user monthly invoice
  start_date = addToDate(next_period_date, to_add={'month': -1})
  assert hosting_subscription.getNextPeriodicalDate(start_date) == next_period_date
else:
  raise ValueError('Unsupported quantity unit %s' % subscription_request.getQuantityUnit())

open_order_edit_kw = dict(
  title=hosting_subscription.getTitle(),
  start_date=start_date,
  effective_date=subscription_request.getEffectiveDate(),
  specialise_value=subscription_request.getSpecialiseValue(),
  source_value=subscription_request.getSourceValue(),
  source_section_value=subscription_request.getSourceSectionValue(),
  source_decision_value=subscription_request.getSourceDecisionValue(),
  source_project_value=subscription_request.getSourceProjectValue(),
  destination_value=subscription_request.getDestinationValue(),
  destination_section_value=subscription_request.getDestinationSectionValue(),
  destination_decision_value=subscription_request.getDestinationDecisionValue(),
  destination_project_value=subscription_request.getDestinationProjectValue(),
  ledger_value=portal.portal_categories.ledger.automated,
  causality_value=subscription_request,
  price_currency_value=subscription_request.getPriceCurrencyValue(),
  activate_kw=activate_kw
)

open_sale_order = portal.open_sale_order_module.newContent(
  portal_type="Open Sale Order",

  # Do not set the stop_date, as we don't know
  # when the user will close the subscription
  stop_date=None,

  **open_order_edit_kw
)

variation_category_list = subscription_request.getVariationCategoryList()
open_order_line = open_sale_order.newContent(
  portal_type="Open Sale Order Line",
  resource_value=subscription_request.getResourceValue(),
  variation_category_list=variation_category_list,
  quantity_unit_value=subscription_request.getQuantityUnitValue(),
  base_contribution_list=subscription_request.getBaseContributionList(),
  use=subscription_request.getUse(),
  activate_kw=activate_kw
)

if variation_category_list:
  base_id = 'path'

  cell_key = list(open_order_line.getCellKeyList(base_id=base_id))[0]
  open_order_cell = open_order_line.newCell(
    base_id=base_id,
    portal_type="Open Sale Order Cell",
    *cell_key
  )
  open_order_cell.edit(
    mapped_value_property_list=['price','quantity'],
    predicate_category_list=cell_key,
    variation_category_list=cell_key,
    activate_kw=activate_kw
  )
else:
  open_order_cell = open_order_line

open_order_cell.edit(
  quantity=subscription_request.getQuantity(),
  price=subscription_request.getPrice(),
  aggregate_value_list=[
    hosting_subscription,
    subscription_request.getAggregateValue()
  ],
  activate_kw=activate_kw
)

open_sale_order.Delivery_fixBaseContributionTaxableRate()
open_sale_order.Base_checkConsistency()
open_sale_order.plan()
open_sale_order.validate()

#######################################################
# Discount
open_order_cell.OpenSaleOrderCell_createDiscountSalePackingList(
  current_date,
  "first invoice discount for %s" % open_sale_order.getReference(),
  subscription_request,
  activate_kw=activate_kw
)

return open_sale_order
