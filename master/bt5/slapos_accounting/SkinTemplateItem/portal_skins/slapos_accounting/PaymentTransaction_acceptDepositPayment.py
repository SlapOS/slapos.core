from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from DateTime import DateTime
from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
payment_transaction = context

assert payment_transaction.getSimulationState() == 'stopped'
trade_condition = payment_transaction.getSpecialiseValue()
assert trade_condition is not None
assert trade_condition.getTradeConditionType() == 'deposit'
# Ensure the payment has no grouping reference
assert not [x for x in trade_condition.contentValues(portal_type='Accounting Transaction Line') if x.getGroupingReference(None) is not None]

start_date = DateTime()
stop_date = None

resource_value = portal.restrictedTraverse('service_module/slapos_deposit')
quantity_unit_value = resource_value.getQuantityUnitValue()

order_portal_type = 'Sale Packing List'
order_line_portal_type = 'Sale Packing List Line'

existing_packing_list = portal.portal_catalog.getResultValue(
  portal_type=order_portal_type,
  causality__uid=payment_transaction.getUid()
)
if existing_packing_list is not None:
  return

#######################################################
# Open Sale Order
#raise NotImplementedError('Fix dates')
open_sale_order = portal.getDefaultModule(portal_type=order_portal_type).newContent(
  portal_type=order_portal_type,
  start_date=start_date,
  stop_date=stop_date,
  specialise_value=payment_transaction.getSpecialiseValue(),
  source_value=payment_transaction.getSourceValue(),
  source_section_value=payment_transaction.getSourceSectionValue(),
  source_decision_value=payment_transaction.getSourceDecisionValue(),
  source_project_value=payment_transaction.getSourceProjectValue(),
  destination_value=payment_transaction.getDestinationValue(),
  destination_section_value=payment_transaction.getDestinationSectionValue(),
  destination_decision_value=payment_transaction.getDestinationDecisionValue(),
  destination_project_value=payment_transaction.getDestinationProjectValue(),
  ledger_value=payment_transaction.getLedgerValue(),
  causality_value=payment_transaction,
  price_currency_value=payment_transaction.getResourceValue(),
  activate_kw=activate_kw
)


open_sale_order.newContent(
  portal_type=order_line_portal_type,
  resource_value=resource_value,
  quantity_unit_value=quantity_unit_value,
  base_contribution_list=resource_value.getBaseContributionList(),
  use=resource_value.getUse(),

  quantity=1,
  #price=-payment_transaction.getTotalPrice(),
  price=-payment_transaction.PaymentTransaction_getTotalPayablePrice(),

  activate_kw=activate_kw
)

open_sale_order.confirm(comment=translateString("Deposit payment accepted."))
open_sale_order.stop(comment=translateString("Deposit payment accepted."))
open_sale_order.deliver(comment=translateString("Deposit payment accepted."))

return open_sale_order
