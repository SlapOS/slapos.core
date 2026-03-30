portal = context.getPortalObject()
result_list = []

migration_kw = {
  'portal_type': 'Sale Trade Condition',
  'validation_state': 'validated',
  'ledger__uid': portal.portal_categories.ledger.automated.getUid(),
  'trade_condition_type__uid': portal.portal_categories.trade_condition_type.compute_node.getUid(),
  'effective_date': None
}

non_migrated_instance = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_instance) == 1:
  result_list.append("all X needs updates %s" % non_migrated_instance[0].getRelativeUrl())
  if fixit:
    tag = script.getId()
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5,
                       tag=tag,
                       after_method_id=('immediateReindexObject',
                                        'recursiveImmediateReindexObject')),
      method_kw={'tag': tag},
      method_id='SaleTradeCondition_archiveIfComputeNodeTradeConditionType',
      **migration_kw)
return result_list
