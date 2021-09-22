portal = context.getPortalObject()
result_list = []

migration_kw = {
  'portal_type': 'Computer',
}

non_migrated_instance = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_instance) == 1:
  if fixit:
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5,
                       tag=script.getId(),
                       after_method_id=('immediateReindexObject',
                                        'recursiveImmediateReindexObject')),
      method_id='fixConsistency',
      **migration_kw)
  else:
    result_list.append("all X needs updates %s" % non_migrated_instance[0].getRelativeUrl())

return result_list
