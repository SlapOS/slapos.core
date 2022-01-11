from DateTime import DateTime
from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()

######################################################
# Find Sale Trade Condition
source_section = context

# Create a temp Sale Order to calculate the real price and find the trade condition
now = DateTime()
module = portal.portal_trash


tmp_sale_order = module.newContent(
  portal_type='Sale Order',
  temp_object=True,
  trade_condition_type="deposit",
  start_date=now,
  destination_value=source_section,
  destination_section_value=source_section,
  destination_decision_value=source_section,
  ledger_value=portal.portal_categories.ledger.automated,
  price_currency=currency_relative_url
)
tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)

if tmp_sale_order.getSpecialise(None) is None:
  raise AssertionError('Can not find a trade condition to generate the Payment Transaction')

if currency_relative_url != tmp_sale_order.getPriceCurrency():
  raise AssertionError('Unexpected different currency: %s %s' % (currency_relative_url, tmp_sale_order.getPriceCurrency()))

# If no accounting is needed, no need to check the price
if (tmp_sale_order.getSourceSection(None) == tmp_sale_order.getDestinationSection(None)) or \
  (tmp_sale_order.getSourceSection(None) is None):
  raise AssertionError('The trade condition does not generate accounting: %s' % tmp_sale_order.getSpecialise())


#######################################################
payment_transaction = portal.accounting_module.newContent(
  title="reservation payment",
  portal_type="Payment Transaction",
  start_date=now,
  stop_date=now,

  specialise_value=tmp_sale_order.getSpecialiseValue(),
  source=tmp_sale_order.getSource(),
  source_section=tmp_sale_order.getSourceSection(),
  source_decision=tmp_sale_order.getSourceDecision(),
  source_project=tmp_sale_order.getSourceProject(),
  destination=tmp_sale_order.getDestination(),
  destination_section=tmp_sale_order.getDestinationSection(),
  destination_decision=tmp_sale_order.getDestinationDecision(),
  destination_project=tmp_sale_order.getDestinationProject(),

  ledger_value=portal.portal_categories.ledger.automated,
  resource=tmp_sale_order.getPriceCurrency(),
  created_by_builder=1, # XXX this prevent init script from creating lines.
  activate_kw={'tag':'%s_init' % context.getRelativeUrl()}
)

getAccountForUse = context.Base_getAccountForUse

# receivable
payment_transaction.newContent(
  id='receivable',
  portal_type='Accounting Transaction Line',
  quantity=price,
  source_value=getAccountForUse('asset_receivable_subscriber'),
  destination_value=getAccountForUse('payable')
)

# bank
collection_account = getAccountForUse('collection')
payment_transaction.newContent(
  id='bank',
  portal_type='Accounting Transaction Line',
  quantity=-price,
  source_value=collection_account,
  destination_value=collection_account
)

if len(payment_transaction.checkConsistency()) != 0:
  raise AssertionError(payment_transaction.checkConsistency()[0])

#tag = '%s_update' % context.getDestinationReference()

comment = translateString("Deposit payment.")
payment_transaction.start(comment=comment)

return payment_transaction
