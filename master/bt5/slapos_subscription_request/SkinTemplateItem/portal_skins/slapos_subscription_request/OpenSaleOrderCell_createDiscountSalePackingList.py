from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
open_sale_order_cell = context
hosting_subscription = open_sale_order_cell.getAggregateValue(portal_type='Hosting Subscription')

open_sale_order = open_sale_order_cell.getParentValue()
if open_sale_order_cell.getPortalType() == 'Open Sale Order Cell':
  open_sale_order = open_sale_order.getParentValue()

start_date = open_sale_order.getStartDate()
next_period_date = hosting_subscription.getNextPeriodicalDate(current_date)

if open_sale_order.getValidationState() == 'validated':
  unused_day_count = current_date - start_date
elif open_sale_order.getValidationState() == 'archived':
  unused_day_count = next_period_date - current_date
else:
  raise NotImplementedError('Unhandled open order state: %s' % open_sale_order.getValidationState())

sale_packing_list_edit_kw = dict(
  title=title,
  start_date=start_date,
  # It should match the first open order invoice
  stop_date=next_period_date,
  specialise_value=open_sale_order.getSpecialiseValue(),
  source_value=open_sale_order.getSourceValue(),
  source_section_value=open_sale_order.getSourceSectionValue(),
  source_decision_value=open_sale_order.getSourceDecisionValue(),
  source_project_value=open_sale_order.getSourceProjectValue(),
  destination_value=open_sale_order.getDestinationValue(),
  destination_section_value=open_sale_order.getDestinationSectionValue(),
  destination_decision_value=open_sale_order.getDestinationDecisionValue(),
  destination_project_value=open_sale_order.getDestinationProjectValue(),
  ledger_value=open_sale_order.getLedgerValue(),
  causality_value=causality_value,
  price_currency_value=open_sale_order.getPriceCurrencyValue(),
  activate_kw=activate_kw
)



if (0 < unused_day_count):
  # If the open order starts before today,
  # generate a discount to the user on his next invoice
  # and reduce the stock consumption

  sale_packing_list = portal.sale_packing_list_module.newContent(
    portal_type="Sale Packing List",
    comment="%s unused days of %s" % (unused_day_count, next_period_date-start_date),
    **sale_packing_list_edit_kw
  )

  variation_category_list = open_sale_order_cell.getVariationCategoryList()
  sale_packing_list_line = sale_packing_list.newContent(
    portal_type="Sale Packing List Line",
    resource_value=open_sale_order_cell.getResourceValue(),
    variation_category_list=variation_category_list,
    quantity_unit_value=open_sale_order_cell.getQuantityUnitValue(),
    base_contribution_list=open_sale_order_cell.getResourceValue().getBaseContributionList(),
    use=open_sale_order_cell.getResourceValue().getUse(),
    activate_kw=activate_kw
  )

  if variation_category_list:
    base_id = 'movement'

    cell_key = list(sale_packing_list_line.getCellKeyList(base_id=base_id))[0]
    sale_packing_list_cell = sale_packing_list_line.newCell(
      base_id=base_id,
      portal_type="Sale Packing List Cell",
      *cell_key
    )
    sale_packing_list_cell.edit(
      mapped_value_property_list=['price','quantity'],
      predicate_category_list=cell_key,
      variation_category_list=cell_key,
      activate_kw=activate_kw
    )
  else:
    sale_packing_list_cell = sale_packing_list_line

  quantity = open_sale_order_cell.getQuantity() * (unused_day_count / (next_period_date - start_date))
  # precision = context.getQuantityPrecisionFromResource(open_sale_order_cell.getResourceValue())
  # XXX Stock does not seem to use quantity unit precision...
  precision = 2
  # Use currency precision to reduce the float length
  quantity = float(('%%0.%sf' % precision) % quantity)

  aggregate_value_list = [x for x in open_sale_order_cell.getAggregateValue() if (x.getPortalType() != 'Hosting Subscription')]
  sale_packing_list_cell.edit(
    # Quantity is negative, to reduce the stock of the consumed product
    quantity=-quantity,
    price=open_sale_order_cell.getPrice(),
    aggregate_value_list=aggregate_value_list,
    activate_kw=activate_kw
  )

  sale_packing_list.Delivery_fixBaseContributionTaxableRate()
  sale_packing_list.Base_checkConsistency()
  sale_packing_list.confirm()
  sale_packing_list.stop()
  sale_packing_list.deliver()
  return sale_packing_list
