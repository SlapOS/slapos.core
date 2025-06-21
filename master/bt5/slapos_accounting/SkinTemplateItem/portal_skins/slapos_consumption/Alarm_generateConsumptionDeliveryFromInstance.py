portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  parent_uid=portal.software_instance_module.getUid(),
  validation_state='validated',
  method_id='SoftwareInstance_generateConsumptionDelivery',
  packet_size=1,
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
