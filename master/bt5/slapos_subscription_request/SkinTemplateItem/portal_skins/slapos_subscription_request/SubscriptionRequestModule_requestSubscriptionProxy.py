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
       person.getDefaultEmailText(),
       user_input_dict["amount"],
       subscription_reference))

target_language = context.getPortalObject().Localizer.get_selected_language()

subscription_request = context.subscription_request_module.newContent(
  portal_type="Subscription Request",
  destination_section_value=person,
  quantity=user_input_dict["amount"],
  language=target_language
)

subscription_request.setDefaultEmailText(email)


def wrapWithShadow(subscription_request, amount, subscription_reference):
  subscription_request.activate(tag="subscription_condition_%s" % subscription_request.getId()
                             ).SubscriptionRequest_applyCondition(subscription_reference, target_language)
  return subscription_request.SubscriptionRequest_requestPaymentTransaction(
    amount=amount,
    tag="subscription_%s" % subscription_request.getId(),
    target_language=target_language
  )

payment = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[subscription_request, user_input_dict["amount"], subscription_reference])

if batch_mode:
  return {'subscription' : subscription_request.getRelativeUrl(), 'payment': payment.getRelativeUrl() }

if target_language == "zh": # Wechat payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site)
else: # Payzen payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site)

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapRedirectWithShadow,
  argument_list=[payment, web_site])
