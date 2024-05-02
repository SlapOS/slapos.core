portal = context.getPortalObject()
from DateTime import DateTime

date = DateTime()
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()

outstanding_amount = context
web_site = context.getWebSiteValue()

assert web_site is not None
assert outstanding_amount.getLedgerUid() == portal.portal_categories.ledger.automated.getUid()
assert outstanding_amount.getDestinationSectionUid() == entity.getUid()

payment_mode = None
resource_uid = outstanding_amount.getPriceCurrencyUid()
for accepted_resource_uid, accepted_payment_mode, is_activated in [
  (portal.currency_module.EUR.getUid(), 'payzen', portal.Base_getPayzenServiceRelativeUrl()),
]:
  if is_activated and (resource_uid == accepted_resource_uid):
    payment_mode = accepted_payment_mode

assert payment_mode is not None

def wrapWithShadow(entity, outstanding_amount):
  return entity.Entity_createPaymentTransaction(
    entity.Entity_getOutstandingAmountList(
      section_uid=outstanding_amount.getSourceSectionUid(),
      resource_uid=outstanding_amount.getPriceCurrencyUid(),
      ledger_uid=outstanding_amount.getLedgerUid(),
      group_by_node=False
    ),
    start_date=date,
    payment_mode=payment_mode
  )

entity = outstanding_amount.getDestinationSectionValue(portal_type="Person")

payment_transaction = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=wrapWithShadow,
  argument_list=[entity, outstanding_amount])

web_site = context.getWebSiteValue()

if (payment_mode == "wechat"):
  return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site=web_site)
elif (payment_mode == "payzen"):
  return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site=web_site)
else:
  raise NotImplementedError('not implemented')
