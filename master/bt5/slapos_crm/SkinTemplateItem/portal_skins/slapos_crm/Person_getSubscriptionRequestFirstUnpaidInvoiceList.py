portal = context.getPortalObject()
from erp5.component.module.DateUtils import addToDate
from Products.ZSQLCatalog.SQLCatalog import Query
from DateTime import DateTime

unpaid_list = []
subscription_request_list = portal.portal_catalog(
  portal_type="Subscription Request",
  simulation_state=["ordered", "confirmed"],
  default_destination_section_uid=context.getUid(),
  # Select "Subscription Request" with most likely unpaid invoices, recently generated.
  creation_date=Query(creation_date=addToDate(DateTime(), to_add={'day': -20}), range="min"))

for subscription_request in subscription_request_list:
  first_invoice = subscription_request.SubscriptionRequest_verifyPaymentBalanceIsReady()
  if first_invoice is not None and not first_invoice.SaleInvoiceTransaction_isLettered():
    unpaid_list.append(first_invoice)

return unpaid_list
