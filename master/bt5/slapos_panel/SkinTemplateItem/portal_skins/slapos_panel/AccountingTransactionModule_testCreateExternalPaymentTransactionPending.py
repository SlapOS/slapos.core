"""
  Test if there is something to pay.

  If `return_message` is true, return "nothing to pay or contact us to pay",
   otherwise the form should display a listbox, and not rely on the message.
"""
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

NOTHING_TO_PAY = context.Base_translateString('Nothing to pay')
NOTHING_TO_PAY_NO_PERSON = context.Base_translateString('Nothing to pay with your account')
PLEASE_CONTACT_US = context.Base_translateString('Please contact us to handle your payment')

# This script will be used to generate the payment
# compatible with external providers
entity = portal.portal_membership.getAuthenticatedMember().getUserValue()
if entity is None:
  if return_message:
    return NOTHING_TO_PAY_NO_PERSON
  return False

kw = {'ledger_uid': portal.portal_categories.ledger.automated.getUid()}
for currency_uid, secure_service_relative_url in context.Base_getSupportedExternalPaymentList():
  if not return_message and secure_service_relative_url is None:
    # We should never get message from an unconfigured site,
    # else we will over calculate, so return as early as possible.
    return False

  kw['resource_uid'] = currency_uid
  for method in [
        entity.Entity_getOutstandingAmountList,
        entity.Entity_getOutstandingDepositAmountList]:
    for outstanding_amount in method(**kw):
      if 0 < outstanding_amount.total_price:
        if return_message:
          assert secure_service_relative_url, \
            "Payment is configured (and should not)"
          return PLEASE_CONTACT_US
        return True

if return_message:
  return NOTHING_TO_PAY

return False
