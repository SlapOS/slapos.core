from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
web_site = context.getWebSiteValue()
assert web_site is not None

ledger_uid = portal.portal_categories.ledger.automated.getUid()

# This script will be used to generate the payment
# compatible with external providers

html_content = ''
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  return '<p>Nothing to pay with your account</p>'

is_payment_configured = 1
for currency_uid, secure_service_relative_url in [
  (portal.currency_module.EUR.getUid(), portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, portal.Base_getWechatServiceRelativeUrl())
]:
  if secure_service_relative_url is None:
    is_payment_configured = 0

  for method in [entity.Entity_getOutstandingAmountList,
                  entity.Entity_getOutstandingDepositAmountList]:
    for outstanding_amount in method(
         ledger_uid=ledger_uid, resource_uid=currency_uid):
      if 0 < outstanding_amount.total_price:
        if not is_payment_configured:
          return '<p>Please contact us to handle your payment</p>'

        html_content += """
          <p><a href="%(payment_url)s">%(total_price)s %(currency)s</a></p>
          """ % {
            'total_price': outstanding_amount.total_price,
            'currency': outstanding_amount.getPriceCurrencyReference(),
            'payment_url': '%s/Base_createExternalPaymentTransactionFromOutstandingAmountAndRedirect' % outstanding_amount.absolute_url()
          }

if not html_content:
  html_content = '<p>Nothing to pay</p>'

return html_content
