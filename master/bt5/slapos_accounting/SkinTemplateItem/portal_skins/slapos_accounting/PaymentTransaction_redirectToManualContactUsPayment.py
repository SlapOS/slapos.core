""" Return a dict with vads_urls required for payzen."""
if web_site is None:
  web_site = context.getWebSiteValue()

if context.PaymentTransaction_getTotalPayablePrice() == 0:
  # This script cannot be used if Payment has a value to pay
  raise ValueError("Payment Transaction has a non zero total")

base_url = web_site.absolute_url()
payment_transaction_url = context.getRelativeUrl()

base = web_site.getLayoutProperty("configuration_payment_url_template",
                                 "%(url)s/#/%(payment_transaction_url)s?page=slap_payment_result&result=%(result)s")

base_substitution_dict = {
  "url" : base_url,
  "payment_transaction_url": payment_transaction_url,
  "result": "contact_us"
}

redirect_url = base % base_substitution_dict
return context.REQUEST.RESPONSE.redirect(redirect_url)
