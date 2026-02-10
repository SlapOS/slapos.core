from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized


open_sale_order = context
assert open_sale_order.getPortalType() == 'Open Sale Order'
if open_sale_order.getValidationState() != 'validated':
  return

portal = context.getPortalObject()

now = DateTime()
if now < open_sale_order.getSpecialiseValue().getExpirationDate(now):
  return

# Create new Open Sale Order using the new STC
line_list = []
for open_order_line in open_sale_order.contentValues(portal_type='Open Sale Order Line'):
  if open_order_line.getAggregate(None) is None:
    for open_order_cell in open_order_line.contentValues(portal_type='Open Sale Order Cell'):
      line_list.append(open_order_cell)
  else:
    line_list.append(open_order_line)

if len(line_list) != 1:
  # Can not handle Open Order with more than 1 line
  return

new_specialise_list = open_sale_order.Base_returnNewEffectiveSaleTradeConditionList()
if new_specialise_list is None:
  # nothing was found, do nothing
  return
if len(new_specialise_list) != 1:
  # Can not handle multiple specialise value
  return

result = None
for open_sale_order_cell in line_list:
  item_value = [x for x in open_sale_order_cell.getAggregateValueList() if x.getPortalType() != 'Hosting Subscription'][0]
  new_specialise_value = portal.restrictedTraverse(new_specialise_list[0])
  result = open_sale_order_cell.getResourceValue().Resource_createSubscriptionRequest(
    open_sale_order.getDestinationValue(),
    # [software_type, software_release],
    open_sale_order_cell.getVariationCategoryList(),
    open_sale_order.getSourceProjectValue(item_value),
    # Keep the previous Open Order price, which may be different
    # from the Sale Supply (it could be manually changed by the Sale Agent)
    forced_subscription_price=open_sale_order_cell.getPrice(),
    currency_value=open_sale_order.getPriceCurrencyValue(),
    portal_type='Subscription Change Request',
    item_value=item_value,
    causality_value=open_sale_order,
    specialise_value=new_specialise_value,
    trade_condition_type=new_specialise_value.getTradeConditionType(),
    activate_kw=activate_kw
  )

# Ensure the price value was kept
# This is a business decision logic: if the price was in a way or another modify for an Open Order,
# keep the human decision as is.
# Sale agents will still be able to change it manually if needed.
if result.getSourceSection() and open_sale_order.getSourceSection():
  # Both subscriptions are payable
  assert result.getPrice() == open_sale_order_cell.getPrice(), result.getPrice()
  assert result.getPriceCurrency() == open_sale_order.getPriceCurrency(), result.getPriceCurrency()
assert result.getSpecialiseValue().getEffectiveDate() == open_sale_order.getSpecialiseValue().getExpirationDate()

return result
