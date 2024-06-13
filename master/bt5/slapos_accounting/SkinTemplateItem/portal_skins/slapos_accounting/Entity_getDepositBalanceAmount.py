portal = context.getPortalObject()

# Ensure all invoice use the same arrow and resource
first_subscription = subscription_list[0]
identical_dict = {
  'getSourceSection': first_subscription.getSourceSection(),
  'getDestinationSection': first_subscription.getDestinationSection(),
  'getPriceCurrency': first_subscription.getPriceCurrency(),
  'getLedger': first_subscription.getLedger(),
}

for subscription in subscription_list:
  for method_id, method_value in identical_dict.items():
    if getattr(subscription, method_id)() != method_value:
      raise ValueError('Subscription Requests do not match on method: %s' % method_id)

  if subscription.getPortalType() != "Subscription Request":
    raise ValueError('Not an Subscription Request')

assert_price_kw = {
  'resource_uid': first_subscription.getPriceCurrencyUid(),
  'portal_type': portal.getPortalAccountingMovementTypeList(),
  'ledger_uid': first_subscription.getLedgerUid(),
}

if first_subscription.getDestinationSection() != context.getRelativeUrl():
  raise ValueError("Subscription not related to the context")

# entity is the depositor
# mirror_section_uid is the payee/recipient
entity_uid = context.getUid()
mirror_section = first_subscription.getSourceSection()

def getUidAsShadow(portal, mirror_section):
  return (
    portal.restrictedTraverse(mirror_section).getUid(),
    portal.restrictedTraverse('account_module/deposit_received').getUid()
  )

person = portal.portal_membership.getAuthenticatedMember().getUserValue()
if person is not None:
  mirror_section_uid, deposit_received_uid = person.Person_restrictMethodAsShadowUser(
    shadow_document=person,
    callable_object=getUidAsShadow,
    argument_list=[portal, mirror_section])
else:
  mirror_section_uid, deposit_received_uid = getUidAsShadow(portal, mirror_section)
# Total received
deposit_amount = portal.portal_simulation.getInventoryAssetPrice(
  section_uid=entity_uid,
  mirror_section_uid=mirror_section_uid,
  mirror_node_uid=deposit_received_uid,
  #node_category_strict_membership=['account_type/income'],
  simulation_state= ('stopped', 'delivered'),
  # Do not gather deposit reimburse
  # when it does not yet have a grouping_reference
  omit_asset_decrease=1,
  grouping_reference=None,
  **assert_price_kw
)

# Total reserved
payable_amount = portal.portal_simulation.getInventoryAssetPrice(
  mirror_section_uid=entity_uid,
  section_uid=mirror_section_uid,
  # Do not gather deposit receivable
  # when it does not yet have a grouping_reference
  omit_asset_decrease=1,
  node_category_strict_membership=['account_type/asset/receivable',
                                   'account_type/liability/payable'],
  simulation_state= ('planned', 'confirmed', 'started', 'stopped', 'delivered'),
  grouping_reference=None,
  **assert_price_kw
)

return deposit_amount - payable_amount
