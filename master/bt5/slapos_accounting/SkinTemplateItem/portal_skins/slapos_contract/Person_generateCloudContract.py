portal = context.getPortalObject()

if context.getPortalType() != "Person":
  raise ValueError("This script can only be called under person context")

payment_portal_type = "Payment Transaction"
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

msg = context.Base_translateString("Cloud Contract related to %s" % context.getTitle())
if (contract is None):
  # Prevent concurrent transaction to create 2 contracts for the same person
  context.serialize()

  # Time to create the contract
  contract = portal.cloud_contract_module.newContent(
    portal_type=contract_portal_type,
    title='Contract for "%s"' % context.getTitle(),
    destination_section_value=context
  )
  contract.validate(comment='New automatic contract for %s' % context.getTitle())
  contract.invalidate(comment='New automatic contract for %s' % context.getTitle())

  contract.reindexObject(activate_kw={'tag': tag})
  msg = context.Base_translateString("Cloud Contract created.")

if (contract.getValidationState() == "invalidated"):

  # search if the user already paid anything
  payment = portal.portal_catalog.getResultValue(
    portal_type=payment_portal_type,
    default_destination_section_uid=context.getUid(),
    simulation_state=['stopped'],
  )

  if (payment is not None):
    # Found one payment, the contract can be validated
    comment = "Contract validated as paid payment %s found" % payment.getRelativeUrl()
    contract.validate(comment=comment)
    contract.reindexObject(activate_kw={'tag': tag})

if batch:
  return contract

return contract.Base_redirect(
   keep_items={"portal_status_message": msg})
