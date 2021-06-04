portal = context.getPortalObject()

migration_kw = {
  'portal_type': ['Software Instance', 'Hosting Subscription'],
  'predecessor__uid': '%'
}

non_migrated_instance = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_instance) == 1:
  print "all X needs updates %s" % non_migrated_instance[0].getRelativeUrl()
  if fixit:
    print "Invoking search and activate to fix all X"
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5,
                       tag=script.getId(),
                       after_method_id=('immediateReindexObject',
                                        'recursiveImmediateReindexObject')),
      method_id='fixConsistency',
      **migration_kw)
return printed
