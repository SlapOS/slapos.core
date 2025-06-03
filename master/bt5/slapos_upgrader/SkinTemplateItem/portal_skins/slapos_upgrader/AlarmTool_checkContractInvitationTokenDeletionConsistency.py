portal = context.getPortalObject()
result_list = []

migration_kw = {
  'portal_type': 'Contract Invitation Token'
}

non_migrated_object = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_object) == 1:
  result_list.append("all X needs updates %s" % non_migrated_object[0].getRelativeUrl())
  if fixit:
    non_migrated_object[0].getParentValue().manage_delObjects(ids=[x.getId() for x in portal.portal_catalog(**migration_kw)])

return result_list
