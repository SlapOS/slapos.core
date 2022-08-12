""" Return a dict with vads_urls required for payzen."""
if web_site is None:
  web_site = context.getWebSiteValue()

if web_site is None:
  raise ValueError("This script must be called from a web site")

base = "%(payment_transaction_url)s/PaymentTransaction_triggerPaymentCheckAlarmAndRedirectToPanel?result=%(result)s"

base_substitution_dict = {
  "payment_transaction_url": context.absolute_url(),
  "result": "__RESULT__"
}

vads_url = base % base_substitution_dict

return dict(
  vads_url_already_registered=vads_url.replace("__RESULT__", "already_registered"),
  vads_url_cancel=vads_url.replace("__RESULT__", "cancel"),
  vads_url_error=vads_url.replace("__RESULT__", "error"),
  vads_url_referral=vads_url.replace("__RESULT__", "referral"),
  vads_url_refused=vads_url.replace("__RESULT__", "refused"),
  vads_url_success=vads_url.replace("__RESULT__", "success"),
  vads_url_return=vads_url.replace("__RESULT__", "return")
)
