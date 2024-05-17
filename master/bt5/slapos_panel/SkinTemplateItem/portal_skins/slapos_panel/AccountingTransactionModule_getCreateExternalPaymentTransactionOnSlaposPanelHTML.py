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
for currency_value, secure_service_relative_url in [
  (portal.currency_module.EUR, portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, portal.Base_getWechatServiceRelativeUrl())
]:
  currency_uid = currency_value.getUid()

  if secure_service_relative_url is None:
    is_payment_configured = 0

  outstanding_amount_list = entity.Entity_getOutstandingAmountList(
    ledger_uid=ledger_uid,
    resource_uid=currency_uid
  )
  for outstanding_amount in outstanding_amount_list:
    if not is_payment_configured:
      return '<p>Please contact us to handle your payment</p>'

    html_content += """
    <p><a href="%(payment_url)s">%(total_price)s %(currency)s</a></p>
    """ % {
      'total_price': outstanding_amount.total_price,
      'currency': outstanding_amount.getPriceCurrencyReference(),
      'payment_url': '%s/SaleInvoiceTransaction_createExternalPaymentTransactionFromAmountAndRedirect' % outstanding_amount.absolute_url()
    }
  outstanding_amount_list = entity.Entity_getOutstandingDepositAmountList(
    resource_uid=currency_uid,
    ledger_uid=ledger_uid
  )
  for outstanding_amount in outstanding_amount_list:
    if 0 < outstanding_amount.total_price:
      if not is_payment_configured:
        return '<p>Please contact us to handle your payment</p>'

      html_content += """
        <p><a href="%(payment_url)s">%(total_price)s %(currency)s</a></p>
        """ % {
          'total_price': outstanding_amount.total_price,
           'currency': currency_value.getReference(),
          'payment_url': '%s/Entity_createExternalPaymentTransactionFromDepositAndRedirect?currency_reference=%s' % (entity.absolute_url(), currency_value.getReference())
        }

if not html_content:
  html_content = '<p>Nothing to pay</p>'

return html_content
