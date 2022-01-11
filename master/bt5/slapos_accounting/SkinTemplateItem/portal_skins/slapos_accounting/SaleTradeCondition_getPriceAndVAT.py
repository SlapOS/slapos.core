from Products.ERP5Type.Cache import CachingMethod
portal = context.getPortalObject()

def getPriceAndVAT():
  assert date is not None
  temp_sale_order = portal.sale_order_module.newContent(
    id=str(DateTime().timeTime()), # XXX: workaround for an obscure transactional cache (?) bug
    temp_object=True,
    portal_type='Sale Order',
    start_date=date,
  )

  temp_sale_order.Order_applyTradeCondition(context)
  temp_sale_order_line = temp_sale_order.newContent(
    id=str(DateTime().timeTime()), # XXX: workaround for an obscure transactional cache (?) bug
    portal_type='Sale Order Line',
    resource_value=resource_value,
    # XXX Try without variation for now
    quantity=quantity,
    price=price
  )
  temp_sale_order_line.setBaseContributionList(resource_value.getBaseContributionList())
  amount_list = temp_sale_order_line.getAggregatedAmountList(rounding=False)
  if len(amount_list) == 0:
    raise ValueError(
      'No amount generated for resource %s with Sale Trade Condition %s' % (
        resource_value.getPath(),
        context.getPath(),
      )
    )
  total_price = temp_sale_order_line.getTotalPrice() or 0.0
  # XXX does not work if quantity === total_price
  amount = [amount for amount in amount_list if amount.getQuantity() == total_price][0]
  return price, amount.getPrice()


cache_index = 0#portal.sale_supply_module.getIntIndex(0)
return CachingMethod(
  getPriceAndVAT,
  id=(script.id, cache_index, context.getRelativeUrl(), resource_value.getRelativeUrl(), date.strftime('%Y%m%d'), quantity),
  cache_factory='erp5_content_long',
)()
