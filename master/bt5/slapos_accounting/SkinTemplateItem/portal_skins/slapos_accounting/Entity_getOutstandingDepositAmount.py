from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ledger_uid = portal.portal_categories.ledger.automated.getUid()

if not currency_uid:
  raise ValueError("You must provide an currency to calculate the amount")

outstanding_amount_list = context.Entity_getOutstandingDepositAmountList(
  resource_uid=currency_uid, ledger_uid=ledger_uid)

if not outstanding_amount_list:
  # Nothing found
  return 0

if len(outstanding_amount_list) > 1:
  raise ValueError('More them one value for the %s currency was found' % currency_uid)

return outstanding_amount_list[0].total_price
