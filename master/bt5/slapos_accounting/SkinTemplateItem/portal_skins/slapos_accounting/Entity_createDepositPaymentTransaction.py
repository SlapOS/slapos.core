from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from DateTime import DateTime
from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()

if not subscription_list:
  raise ValueError('You need to provide at least one Subscription Request')

payment_tag = 'Entity_addDepositPayment_%s' % context.getUid()
if context.REQUEST.get(payment_tag, None) is not None:
  raise ValueError('This script was already called twice on the same transaction ')
activate_kw = {
  'tag': payment_tag
}

# Ensure all invoice use the same arrow and resource
first_subscription = subscription_list[0]
identical_dict = {
  'getSource': first_subscription.getSource(),
  'getSourceSection': first_subscription.getSourceSection(),
  'getDestinationSection': first_subscription.getDestinationSection(),
  'getPriceCurrency': first_subscription.getPriceCurrency(),
  'getLedger': first_subscription.getLedger(),
}

price = 0
for subscription in subscription_list:
  for method_id, method_value in identical_dict.items():
    if getattr(subscription, method_id)() != method_value:
      raise ValueError('Subscription Requests do not match on method: %s' % method_id)
  if subscription.total_price:
    price += subscription.total_price

  # Simulation state
  if not subscription.isTempObject() and subscription.getSimulationState() != "submitted":
    raise ValueError('Not on submitted state')

  if subscription.getPortalType() != "Subscription Request":
    raise ValueError('Not an Subscription Request')

if not price:
  raise ValueError("No price to to pay")

if first_subscription.getDestinationSection() != context.getRelativeUrl():
  raise ValueError("Subscription not related to the context")

######################################################
# Find Sale Trade Condition
source_section = context
currency_relative_url = first_subscription.getPriceCurrency()
ledger_relative_url = first_subscription.getLedger()

# Create a temp Sale Order to calculate the real price and find the trade condition
now = DateTime()
module = portal.portal_trash

tmp_sale_order = module.newContent(
  portal_type='Sale Order',
  temp_object=True,
  trade_condition_type="deposit",
  start_date=now,
  source=first_subscription.getSource(),
  source_section=first_subscription.getSourceSection(),
  destination_value=source_section,
  destination_section_value=source_section,
  destination_decision_value=source_section,
  ledger=ledger_relative_url,
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
# The payment needs to be returned on web site context, to proper handle acquisition later on
# otherwise, payment redirections would fail on multiple occasions whenever website isn't in
# the context acquisition.
web_site = context.getWebSiteValue()
if web_site is None:
  web_site = portal

# preserve the capability to call payment_transaction.getWebSiteValue() and get the current website back.
payment_transaction = web_site.accounting_module.newContent(
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
  payment_mode=payment_mode,
  ledger_value=ledger_relative_url,
  resource=tmp_sale_order.getPriceCurrency(),
  created_by_builder=1, # XXX this prevent init script from creating lines.
  activate_kw=activate_kw
)

getAccountForUse = context.Base_getAccountForUse

# receivable
payment_transaction.newContent(
  id='receivable',
  portal_type='Accounting Transaction Line',
  quantity=price,
  source_value=getAccountForUse('asset_receivable_subscriber'),
  destination_value=getAccountForUse('payable'),
  activate_kw=activate_kw
)

# bank
collection_account = getAccountForUse('collection')
payment_transaction.newContent(
  id='bank',
  portal_type='Accounting Transaction Line',
  quantity=-price,
  source_value=collection_account,
  destination_value=collection_account,
  activate_kw=activate_kw
)

if len(payment_transaction.checkConsistency()) != 0:
  raise AssertionError(payment_transaction.checkConsistency()[0])

payment_transaction.start(comment=translateString("Deposit payment."))

# Set a flag on the request for prevent 2 calls on the same transaction
context.REQUEST.set(payment_tag, 1)

return payment_transaction
