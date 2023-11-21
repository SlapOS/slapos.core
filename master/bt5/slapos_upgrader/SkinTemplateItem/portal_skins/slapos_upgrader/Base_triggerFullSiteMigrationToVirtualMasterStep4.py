# create the software products
################################################
portal = context.getPortalObject()

tag = script.id

############################################
# Create products per project
############################################
portal.portal_catalog.searchAndActivate(
  method_id='Project_checkSoftwareProductToVirtualMaster',
  method_kw={'activate_kw': {'tag': tag}},
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Project",
)

############################################
# Create instance node per project
############################################
portal.portal_catalog.searchAndActivate(
  method_id='Project_checkInstanceNodeToVirtualMaster',
  method_kw={'activate_kw': {'tag': tag}},
  activate_kw={'tag': tag, 'priority': 1},

  portal_type="Project",
)

context.activate(after_tag=tag, priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep5()
