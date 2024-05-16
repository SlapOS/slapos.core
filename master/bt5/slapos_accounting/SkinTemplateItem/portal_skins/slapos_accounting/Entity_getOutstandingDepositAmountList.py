portal = context.getPortalObject()
from Products.ERP5Type.Document import newTempBase

query_kw = {
  "portal_type": "Subscription Request",
  "simulation_state": "submitted"
}

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
    currency = subscription_request.getPriceCurrency()
    # Future proof in case we implement B2B payment
    object_index = "%s_%s" % (currency, subscription_request.getDestinationSection())
    if object_index not in object_dict:
      object_dict[object_index] = dict(
        causality_list=[],
        uid=object_index,
        price_currency=currency,
        destination_section=subscription_request.getDestinationSection(),
        total_price = 0)

    object_dict[object_index]['total_price'] = \
      object_dict[object_index]['total_price'] + subscription_request_total_price
    
    object_dict[object_index]['causality_list'].append(subscription_request.getRelativeUrl())

object_list = []
for key in object_dict:
  object_list.append(newTempBase(
    portal, object_dict[key]['causality_list'][0], **object_dict[key])) 

return object_list
