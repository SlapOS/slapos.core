portal = context.getPortalObject()
result_list = []

migration_kw = {
  'portal_type': ['Software Instance', 'Hosting Subscription'],
  'predecessor__uid': '%'
}

non_migrated_instance = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_instance) == 1:
  result_list.append("all X needs updates %s" % non_migrated_instance[0].getRelativeUrl())
  if fixit:
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5,
                       tag=script.getId(),
                       after_method_id=('immediateReindexObject',
                                        'recursiveImmediateReindexObject')),
      method_id='fixConsistency',
      **migration_kw)
return result_list
