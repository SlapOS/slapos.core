from zExceptions import Unauthorized
from DateTime import DateTime
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

web_site = context.getWebSiteValue()
if email in ["", None]:
  error = "Email must be provided"
  base_url = context.getWebSectionValue().absolute_url()
  redirect_url = "%s?field_your_reservation_name=%s&field_your_reservation_email=%s&field_your_reservation_number_of_machines=%s&field_your_reservation_network=%s&field_your_reservation_invitation_token=%s&portal_status_message=%s" % (
      base_url,
      user_input_dict['name'],
      email,
      user_input_dict["amount"],
      subscription_reference,
      token,
      error
      )
  return context.REQUEST.RESPONSE.redirect(redirect_url)

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
    base_url = context.getWebSectionValue().absolute_url()
    redirect_url = "%s?field_your_reservation_name=%s&field_your_reservation_email=%s&field_your_reservation_number_of_machines=%s&field_your_reservation_network=%s&field_your_reservation_invitation_token=%s&portal_status_message=%s" % (
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
  redirect_url = "%s/order_confirmation?field_your_reservation_name=%s&field_your_reservation_email=%s&field_your_reservation_number_of_machines=%s&field_your_reservation_network=%s" % (
       base_url,
       person.getTitle(),
       person.getDefaultEmailText(),
       user_input_dict["amount"],
       subscription_reference)
  if token:
    redirect_url += "&field_your_reservation_invitation_token=%s" % token
  if variation_reference:
    redirect_url += "&field_your_variation_reference=%s" % variation_reference
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

def wrapWithShadow(subscription_request, subscription_reference,
                   subscription_request_id, variation_reference, contract=contract):
  subscription_request.activate(tag="subscription_condition_%s" % subscription_request_id
                             ).SubscriptionRequest_applyCondition(subscription_reference, target_language)
  return subscription_request.SubscriptionRequest_requestPaymentTransaction(
    tag="subscription_%s" % subscription_request_id,
    target_language=target_language,
    contract=contract,
    variation_reference=variation_reference
  )

payment = person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[subscription_request, 
                 subscription_reference, subscription_request.getId(),
                 variation_reference, contract])

if batch_mode:
  return {'subscription' : subscription_request.getRelativeUrl(),
          'payment': payment.getRelativeUrl() }

if target_language == "zh": # Wechat payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    # getTotalPayble returns a negative value
    if payment_transaction.PaymentTransaction_getTotalPayablePrice() < 0:
      if payment_transaction.Base_getWechatServiceRelativeUrl():
        return payment_transaction.PaymentTransaction_redirectToManualWechatPayment(web_site)
      return payment_transaction.PaymentTransaction_redirectToManualContactUsPayment(web_site)
    return payment_transaction.PaymentTransaction_redirectToManualFreePayment(web_site)
    
else: # Payzen payment
  def wrapRedirectWithShadow(payment_transaction, web_site):
    # getTotalPayble returns a negative value
    if payment_transaction.PaymentTransaction_getTotalPayablePrice() < 0:
      if payment_transaction.Base_getPayzenServiceRelativeUrl():
        return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment(web_site)
      return payment_transaction.PaymentTransaction_redirectToManualContactUsPayment(web_site)
    return payment_transaction.PaymentTransaction_redirectToManualFreePayment(web_site)
    
return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapRedirectWithShadow,
  argument_list=[payment, web_site])
