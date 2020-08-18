from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if cloud_invitation is None:
  return None

portal = context.getPortalObject()
contract_portal_type = "Cloud Contract"

tag = "%s_requestValidationPayment_inProgress" % context.getUid()
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The cloud contract is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  return None

contract = portal.portal_catalog.getResultValue(
  portal_type=contract_portal_type,
  default_destination_section_uid=context.getUid(),
  validation_state=['invalidated', 'validated'],
)

if (contract is None):
  # Prevent concurrent transaction to create 2 contracts for the same context
  context.serialize()

  # Time to create the contract
  contract = portal.cloud_contract_module.newContent(
    portal_type=contract_portal_type,
    title='Contract for "%s"' % context.getTitle(),
    destination_section_value=context
  )
  contract.validate(comment='New automatic contract for %s (token: %s)' % 
      (context.getTitle(), cloud_invitation.getTitle()))
  contract.reindexObject(activate_kw={'tag': tag})

if (contract.getValidationState() == "invalidated"):
  contract.validate(comment='Validation by usaged of the token %s' % (cloud_invitation.getTitle()))
  contract.reindexObject(activate_kw={'tag': tag})

# Cloud invitation maximizes contract, so we keep the maximum value between the 2, we never
# decrease.
if cloud_invitation.getMaximumInvoiceDelay(0) > contract.getMaximumInvoiceDelay(0):
  contract.edit(
    maximum_invoice_delay=cloud_invitation.getMaximumInvoiceDelay())

# Hardcoded Values
for invitation_line in cloud_invitation.objectValues():
  has_line = False
  for line in contract.objectValues():
    if line.getPriceCurrency() == invitation_line.getPriceCurrency() and \
        invitation_line.getMaximumInvoiceCredit(0) > line.getMaximumInvoiceCredit(0):
      line.edit(
         maximum_invoice_credit=invitation_line.getMaximumInvoiceCredit())
      has_line = True
      break
  if not has_line:
    contract.newContent(
      portal_type="Cloud Contract Line",
      maximum_invoice_credit=invitation_line.getMaximumInvoiceCredit(),
      price_currency=invitation_line.getPriceCurrency()
    )    

cloud_invitation.invalidate()
return contract
