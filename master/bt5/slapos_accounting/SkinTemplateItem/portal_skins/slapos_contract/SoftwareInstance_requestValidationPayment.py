from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
software_instance = context
hosting_subscription = software_instance.getSpecialiseValue()
if hosting_subscription is None:
  return
person = hosting_subscription.getDestinationSectionValue(portal_type='Person')
if person is None:
  return

payment_portal_type = "Payment Transaction"
contract_portal_type = "Cloud Contract"

tag = "%s_requestValidationPayment_inProgress" % person.getUid()
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The cloud contract is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  return None

contract = portal.portal_catalog.getResultValue(
  portal_type=contract_portal_type,
  default_destination_section_uid=person.getUid(),
  validation_state=['invalidated', 'validated'],
)

if (contract is None):
  # Prevent concurrent transaction to create 2 contracts for the same person
  person.serialize()

  # Time to create the contract
  contract = portal.cloud_contract_module.newContent(
    portal_type=contract_portal_type,
    title='Contract for "%s"' % person.getTitle(),
    destination_section_value=person
  )
  contract.validate(comment='New automatic contract for %s' % context.getTitle())
  contract.invalidate(comment='New automatic contract for %s' % context.getTitle())

  contract.reindexObject(activate_kw={'tag': tag})

if (contract.getValidationState() == "invalidated"):

  # search if the user already paid anything
  payment = portal.portal_catalog.getResultValue(
    portal_type=payment_portal_type,
    default_destination_section_uid=person.getUid(),
    simulation_state=['stopped'],
  )

  if (payment is not None):
    # Found one payment, the contract can be validated
    comment = "Contract validated as paid payment %s found" % payment.getRelativeUrl()
    contract.validate(comment=comment)
    contract.reindexObject(activate_kw={'tag': tag})

return contract
