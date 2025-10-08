from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

sale_trade_condition = context
if sale_trade_condition.getExpirationDate(None) is not None:
  return

new_specialise_list = context.Base_returnNewEffectiveSaleTradeConditionList()
if new_specialise_list is None:
  # nothing was found, do nothing
  return

# Expire the current trade condition
# and copy a new one, which will use the new version of the expired specialised trade condition
container = sale_trade_condition.getParentValue()
clipboard = container.manage_copyObjects(ids=[sale_trade_condition.getId()])
new_sale_trade_condition = container[container.manage_pasteObjects(clipboard)[0]['new_id']]

new_sale_trade_condition.edit(
  specialise_list=new_specialise_list,
  activate_kw=activate_kw
)
return new_sale_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate().getRelativeUrl()
