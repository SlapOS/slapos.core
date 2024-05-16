portal = context.getPortalObject()

assert_price_kw = {
  'resource_uid': currency_uid,
  'portal_type': portal.getPortalAccountingMovementTypeList(),
  'ledger_uid': portal.portal_categories.ledger.automated.getUid(),
}

# entity is the depositor
# mirror_section_uid is the payee/recipient
entity_uid = context.getUid()

# Total received
deposit_amount = portal.portal_simulation.getInventoryAssetPrice(
  section_uid=entity_uid,
  mirror_section_uid=mirror_section_uid,
  mirror_node_uid=portal.restrictedTraverse('account_module/deposit_received').getUid(),
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
