portal = context.getPortalObject()

query_kw = {
  "portal_type": "Subscription Request",
  "simulation_state": "submitted"
}

if section_uid:
  query_kw['source_section__uid'] = section_uid

if ledger_uid:
  query_kw['ledger__uid'] = ledger_uid

if resource_uid is not None:
  query_kw['price_currency__uid'] = resource_uid

object_dict = {}

for subscription_request_brain in portal.portal_catalog(
  destination_section__uid=context.getUid(),
  **query_kw):

  subscription_request = subscription_request_brain.getObject()
  subscription_request_total_price = subscription_request.getTotalPrice()
  if 0 < subscription_request_total_price:
    currency_uid = subscription_request.getPriceCurrencyUid()
    # Future proof in case we implement B2B payment
    object_index = "%s_%s_%s" % (
      currency_uid,
      subscription_request.getSourceSection(),
      subscription_request.getLedger())
    if object_index not in object_dict:
      object_dict[object_index] = [subscription_request, subscription_request_total_price]
    else:
      subscription_request_total_price += object_dict[object_index][1]
      object_dict[object_index] = [object_dict[object_index][0],
                                   subscription_request_total_price]

# Add the current balance, to ensure customer provide enough deposit to match the VAT
return [s.asContext(total_price=price - s.getDestinationSectionValue().Entity_getDepositBalanceAmount([s])) for s, price in object_dict.values()]
