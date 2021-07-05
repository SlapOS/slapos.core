portal = context.getPortalObject()
from Products.ERP5Type.Document import newTempBase

subscription_trade_condition =  portal.portal_preferences.getPreferredAggregatedSubscriptionSaleTradeCondition()
if subscription_trade_condition is not None:
  specialise_uid = portal.restrictedTraverse(subscription_trade_condition).getUid()
else:
  raise ValueError("Preferences are unconfigured, please update it")

business_process_uid_list = [
  portal.business_process_module.slapos_subscription_business_process.getUid()]

subscription_delivery_specialise_uid_list = [q.getUid() for q in portal.portal_catalog(
  specialise_uid=business_process_uid_list, portal_type='Sale Trade Condition')]

# Recover all Aggregated Sale Packing Lists
aggregated_spl_list = portal.portal_catalog(
  causality_uid=context.getUid(),
  portal_type="Sale Packing List",
  simulation_state="delivered",
  # Hardcoded Value to only recover recent values
  # Replace to acquite value from the template
  source_section_uid=context.organisation_module.rapidspace.getUid(),
  destination_section_uid=context.getDestinationSectionUid(),
  default_specialise_uid=specialise_uid)

temp_invoice_list = []
for aggregated_sale_packing_list in aggregated_spl_list:
  related_invoice_list =  aggregated_sale_packing_list.getCausalityRelatedValueList(
      portal_type="Sale Invoice Transaction")

  assert len(related_invoice_list) == 1, aggregated_sale_packing_list.absolute_url()
  invoice = related_invoice_list[0]

  invoice_dict = dict(
    title=invoice.getTitle(),
    reference=invoice.getReference(),
    start_date=invoice.getStartDate().strftime("%d/%m/%Y"),
    creation_date=invoice.getCreationDate().strftime("%d/%m/%Y"),
    total_price=invoice.getTotalPrice())

  search_kw = {
    'portal_type': 'Sale Packing List Line',
    'simulation_state': 'delivered',
    # Default Aggregate UID to the instance tree?
    "parent_specialise_uid": subscription_delivery_specialise_uid_list,
    "default_aggregate_uid": context.getAggregateUid(),
    'grouping_reference' : aggregated_sale_packing_list.getReference()}

  min_start_date = None
  max_stop_date = None
  quantity = 0

  delivery_line_list = portal.portal_catalog(**search_kw)

  if len(delivery_line_list) == 0:
    if [i for i in aggregated_sale_packing_list.objectValues()
         if i.getResource() != "service_module/slapos_reservation_refund"]:
      raise ValueError(aggregated_sale_packing_list.getRelativeUrl())
    continue

  for sale_packing_list_line in delivery_line_list:
    if not min_start_date:
      min_start_date = sale_packing_list_line.getStartDate()
    else:
      min_start_date = min(min_start_date, sale_packing_list_line.getStartDate())

    if not max_stop_date:
      max_stop_date = sale_packing_list_line.getStopDate()
    else:
      max_stop_date = max(max_stop_date, sale_packing_list_line.getStopDate())

    quantity += sale_packing_list_line.getQuantity()

  invoice_dict.update({
    "begin_date": min_start_date.strftime("%d/%m/%Y"),
    "end_date": max_stop_date.strftime("%d/%m/%Y"),
    "quantity": quantity
  })
  temp_invoice_list.append(
    newTempBase(context.accounting_module, invoice.getId(), **invoice_dict))

return temp_invoice_list
