from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

# You always needs a user here
person, person_is_new = context.SubscriptionRequest_createUser(email, user_input_dict['name'])

web_site = context.getWebSiteValue()
# Check if user is already exist, otherwise redirect to ask confirmation
if confirmation_required and not person_is_new:
  base_url = web_site.absolute_url()

  return context.REQUEST.RESPONSE.redirect(
    "%s/#order_confirmation?name=%s&email=%s&amount=%s&subscription_reference=%s" % (
       base_url,
       person.getTitle(),
       email,
       user_input_dict["amount"],
       subscription_reference))

subscription_request = context.subscription_request_module.newContent(
  portal_type="Subscription Request",
  destination_section_value=person,
  quantity=user_input_dict["amount"]
)

subscription_request.setDefaultEmailText(email)

def wrapWithShadow(subscription_request, amount, subscription_reference):
  subscription_request.activate(tag="subscription_condition_%s" % subscription_request.getId()
                             ).SubscriptionRequest_applyCondition(subscription_reference)
  return subscription_request.SubscriptionRequest_requestPaymentTransaction(amount=amount,
                                                tag="subscription_%s" % subscription_request.getId())

payment = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[subscription_request, user_input_dict["amount"], subscription_reference])

if batch_mode:
  return {'subscription' : subscription_request.getRelativeUrl(), 'payment': payment.getRelativeUrl() }

def wrapGetPriceWithShadow(payment):
  return payment.PaymentTransaction_getTotalPayablePrice()

price = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapGetPriceWithShadow,
  argument_list=[payment,])

# currency = subscription_request.getSpecialiseValue().getPriceCurrency()
# XXX: Test
# currency = "currency_module/EUR"
currency = "currency_module/CNY"

if currency == "currency_module/CNY": # Wechat payment
  '''
  portal = context.getPortalObject()
  code_url = portal.Base_getWechatCodeURL(subscription_request.getId(), price, user_input_dict["amount"])
  web_site = context.getWebSiteValue()
  base_url = web_site.absolute_url()
  return context.REQUEST.RESPONSE.redirect(
    "%s/#wechat_payment?amount=%s&trade_no=%s&code_url=%s" % (base_url, user_input_dict["amount"], subscription_request.getId(), code_url))
  '''
  def wrapRedirectWithShadow(payment_transaction, web_site):
    return payment_transaction.PaymentTransaction_redirectToWechatPayment(web_site)

  return person.Person_restrictMethodAsShadowUser(
    shadow_document=person,
    callable_object=wrapRedirectWithShadow,
    argument_list=[payment, web_site])
else: # "currency_module/EUR", Payzen payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site)

  return person.Person_restrictMethodAsShadowUser(
    shadow_document=person,
    callable_object=wrapRedirectWithShadow,
    argument_list=[payment, web_site])
