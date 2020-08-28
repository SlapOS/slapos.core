from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
web_site = context.getWebSiteValue()
if token:
  error = ""
  try:
    invitation_token = portal.invitation_token_module[token]
  except KeyError:
    error = context.Base_translateString("Token not Found")
  else:
    if invitation_token.getValidationState() != "validated":
      error = "Token is invalid or it was already used"

  if error:
    base_url = web_site.absolute_url()
    redirect_url = "%s/#order?name=%s&email=%s&amount=%s&subscription_reference=%s&token=%s&error=%s" % (
      base_url,
      user_input_dict['name'],
      email,
      user_input_dict["amount"],
      subscription_reference,
      token,
      error
      )
    return context.REQUEST.RESPONSE.redirect(redirect_url)

# You always needs a user here
person, person_is_new = context.SubscriptionRequest_createUser(email, user_input_dict['name'])

# Check if user is already exist, otherwise redirect to ask confirmation
if confirmation_required and not person_is_new:
  base_url = web_site.absolute_url()
  redirect_url = "%s/#order_confirmation?name=%s&email=%s&amount=%s&subscription_reference=%s" % (
       base_url,
       person.getTitle(),
       person.getDefaultEmailText(),
       user_input_dict["amount"],
       subscription_reference)
  if token:
    redirect_url += "&token=%s" % token
  return context.REQUEST.RESPONSE.redirect(redirect_url)

if target_language is None:
  target_language = portal.Localizer.get_selected_language()

contract = None
if token:
  contract = person.Person_applyContractInvitation(invitation_token)

subscription_request = context.subscription_request_module.newContent(
  portal_type="Subscription Request",
  destination_section_value=person,
  quantity=user_input_dict["amount"],
  language=target_language
)

subscription_request.setDefaultEmailText(email)

def wrapWithShadow(subscription_request, amount, subscription_reference,
                   subscription_request_id, contract=contract):
  subscription_request.activate(tag="subscription_condition_%s" % subscription_request_id
                             ).SubscriptionRequest_applyCondition(subscription_reference, target_language)
  return subscription_request.SubscriptionRequest_requestPaymentTransaction(
    amount=amount,
    tag="subscription_%s" % subscription_request_id,
    target_language=target_language,
    contract=contract
  )

payment = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[subscription_request, user_input_dict["amount"],
                 subscription_reference, subscription_request.getId(),
                 contract])

if batch_mode:
  return {'subscription' : subscription_request.getRelativeUrl(),
          'payment': payment.getRelativeUrl() }

if target_language == "zh": # Wechat payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    # getTotalPayble returns a negative value
    if payment_transaction.PaymentTransaction_getTotalPayablePrice() < 0:
      return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site)
    return payment_transaction.PaymentTransaction_redirectToManualFreePayment(web_site)
    
else: # Payzen payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    # getTotalPayble returns a negative value
    if payment_transaction.PaymentTransaction_getTotalPayablePrice() < 0:
      return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site)
    return payment_transaction.PaymentTransaction_redirectToManualFreePayment(web_site)
    
return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapRedirectWithShadow,
  argument_list=[payment, web_site])
