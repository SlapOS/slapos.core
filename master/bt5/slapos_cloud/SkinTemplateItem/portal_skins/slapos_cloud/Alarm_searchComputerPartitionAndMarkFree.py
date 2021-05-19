portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  aggregate__uid="%",
  validation_state="invalidated",
  slap_state="destroy_requested",
  parent_uid=context.getPortalObject().software_instance_module.getUid(),
  method_id='SoftwareInstance_tryToUnallocatePartition',
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
