from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

tag = tag or script.id
sale_trade_condition = context

if sale_trade_condition.getExpirationDate(None) is not None:
  return

if sale_trade_condition.getLedger() != 'automated':
  return

is_compute_node_trade_condition_type = False
trade_condition = sale_trade_condition
while trade_condition is not None:
  if trade_condition.getTradeConditionType() == 'compute_node':
    is_compute_node_trade_condition_type = True
    break
  else:
    trade_condition = trade_condition.getSpecialiseValue(portal_type='Sale Trade Condition')

if not is_compute_node_trade_condition_type:
  return

portal = sale_trade_condition.getPortalObject()
after_tag = '%s.' % tag

portal.portal_catalog.searchAndActivate(
  portal_type='Sale Trade Condition',
  specialise__uid=sale_trade_condition.getUid(),
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  validation_state='validated',

  activate_kw={'tag': after_tag},
  method_kw={'tag': after_tag},
  method_id='SaleTradeCondition_archiveIfComputeNodeTradeConditionType',
)

portal.portal_catalog.searchAndActivate(
  portal_type='Open Sale Order',
  specialise__uid=sale_trade_condition.getUid(),
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  validation_state='validated',

  activate_kw={'tag': after_tag},
  method_kw={'tag': after_tag},
  method_id='OpenSaleOrder_archiveIfComputeNodeTradeConditionType',
)

# archive the trade condition after all dependencies are handled
now = DateTime()
activate_kw = {
  'tag': tag,
  'after_tag': after_tag,
}
sale_trade_condition.activate(**activate_kw).edit(expiration_date=now, activate_kw=activate_kw)

return sale_trade_condition
