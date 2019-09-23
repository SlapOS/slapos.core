from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized


# You always needs a user here
person, person_is_new = context.SubscriptionRequest_createUser(email, user_input_dict['name'])

web_site = context.getWebSiteValue()
# Check if user is already exist, otherwise redirect to ask confirmation

# order.js seems use SubscriptionRequestModule_requestSubscriptionProxy abused...
# In the first time, order.js call SubscriptionRequestModule_requestSubscriptionProxy
# which the "payment_mode" is not selected yet.
# which will use payzen by default
# we should always let user confirm and select payment mode
if confirmation_required:
# if confirmation_required and not person_is_new:
  base_url = web_site.absolute_url()

  return context.REQUEST.RESPONSE.redirect(
    "%s/#order_confirmation?name=%s&email=%s&amount=%s&subscription_reference=%s" % (
       base_url,
       person.getTitle(),
       person.getDefaultEmailText(),
       user_input_dict["amount"],
       subscription_reference))

subscription_request = context.subscription_request_module.newContent(
  portal_type="Subscription Request",
  destination_section_value=person,
  quantity=user_input_dict["amount"]
)

subscription_request.setDefaultEmailText(email)

def wrapWithShadow(subscription_request, amount, subscription_reference, payment_mode):
  subscription_request.activate(tag="subscription_condition_%s" % subscription_request.getId()
                             ).SubscriptionRequest_applyCondition(subscription_reference)

  return subscription_request.SubscriptionRequest_requestPaymentTransaction(amount=amount,
                                                tag="subscription_%s" % subscription_request.getId(), payment_mode=payment_mode)

payment = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[subscription_request, user_input_dict["amount"], subscription_reference, payment_mode])

if batch_mode:
  return {'subscription' : subscription_request.getRelativeUrl(), 'payment': payment.getRelativeUrl() }

if payment_mode == "wechat":
  portal = context.getPortalObject()
  code_url = portal.Base_getWechatCodeURL(subscription_request.getId(), payment.PaymentTransaction_getTotalPayablePrice(), user_input_dict["amount"])
  web_site = context.getWebSiteValue()
  base_url = web_site.absolute_url()
  return context.REQUEST.RESPONSE.redirect(
    "%s/#wechat_payment?amount=%s" % (base_url, user_input_dict["amount"]))

def wrapRedirectWithShadow(payment_transaction, web_site):
  return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site)

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapRedirectWithShadow,
  argument_list=[payment, web_site])
