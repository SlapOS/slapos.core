portal = context.getPortalObject()
id_generator = '_generatePerDayNodeNumberId'
error_list = []

for module_id in portal.objectIds(spec=('ERP5 Folder',)) + ["portal_simulation", "portal_activities"]:
  module = portal.restrictedTraverse(module_id)
  if module.getIdGenerator() != id_generator:

    if fixit:
      error_list.append("%s module has incorrect ID generator (fixed)." % module.getRelativeUrl())
      module.setIdGenerator(id_generator)
    else:
      error_list.append("%s module has incorrect ID generator." % module.getRelativeUrl())

return error_list
