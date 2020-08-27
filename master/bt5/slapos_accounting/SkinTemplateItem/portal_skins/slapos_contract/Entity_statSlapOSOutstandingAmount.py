portal = context.getPortalObject()
from DateTime import DateTime

if contract is None:
  contract = portal.portal_catalog.getResultValue(
    portal_type="Cloud Contract",
    default_destination_section_uid=context.getUid(),
    validation_state=['invalidated', 'validated'],
  )
  if contract is None:
    return context.Entity_statOutstandingAmount()

# We evaluate Multiple scenarios
amount = context.Entity_statOutstandingAmount()
# All payed so just return
if not amount:
  return amount

maximum_invoice_delay = contract.getMaximumInvoiceDelay()
maximum_invoice_credit = 0.0

# For now we only support those 2 currencies
currency_uid_list = [
  portal.currency_module.EUR.getUid(),
  portal.currency_module.CNY.getUid(),
]

for currency_uid in currency_uid_list:
  for line in contract.objectValues(
    portal_type="Cloud Contract Line"):
    if line.getPriceCurrencyUid() == currency_uid:
      maximum_invoice_credit = line.getMaximumInvoiceCredit()
      amount_per_currency = context.Entity_statOutstandingAmount(resource_uid=currency_uid)
      if amount_per_currency > maximum_invoice_credit:
        return amount_per_currency # We exceed maximum amount because
                                   # user already requested too much

if maximum_invoice_delay:
  # Recalculate now ignoring the all invoices from lastest days.
  at_date = DateTime()-maximum_invoice_delay
  return context.Entity_statOutstandingAmount(
      at_date=at_date)

return amount
