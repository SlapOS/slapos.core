portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type=["Slave Instance", "Software Instance"],
  validation_state="validated",
  specialise_validation_state="archived",
  method_id='SoftwareInstance_tryToGarbageCollect',
  activate_kw={'tag': tag},
  **{"slapos_item.slap_state": ("start_requested", "stop_requested")}
)

context.activate(after_tag=tag).getId()
