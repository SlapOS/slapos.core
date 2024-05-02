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

for currency_value, secure_service_relative_url in [
  (portal.currency_module.EUR, portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY, portal.Base_getWechatServiceRelativeUrl())
]:
  currency_uid = currency_value.getCurrencyUid()
  if secure_service_relative_url is not None:
    # Existing invoices
    outstanding_amount_list = entity.Entity_getOutstandingAmountList(
      ledger_uid=ledger_uid,
      resource_uid=currency_uid
    )
    for outstanding_amount in outstanding_amount_list:
      html_content += """
      <p><a href="%(payment_url)s">%(total_price)s %(currency)s</a></p>
      """ % {
        'total_price': outstanding_amount.total_price,
        'currency': outstanding_amount.getPriceCurrencyReference(),
        'payment_url': '%s/SaleInvoiceTransaction_createExternalPaymentTransactionFromAmountAndRedirect' % outstanding_amount.absolute_url()
      }

    deposit_price = entity.Entity_getOutstandingDepositAmount(currency_uid)
    if 0 < deposit_price:
      html_content += """
        <p><a href="%(payment_url)s">%(total_price)s %(currency)s</a></p>
        """ % {
          'total_price': deposit_price,
          'currency': currency_value.getReference(),
          'payment_url': '%s/Entity_createExternalPaymentTransactionFromDepositAndRedirect?currency_reference=%s' % (entity.absolute_url(), currency_value.getReference())
        }

if html_content:
  if web_site.getLayoutProperty("configuration_payment_url_template", None) is None:
    html_content = '<p>Please contact us to handle your payment</p>'
else:
  html_content = '<p>Nothing to pay</p>'

return html_content
