portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type=('Slave Instance', 'Software Instance'),
  validation_state='validated',
  method_id='SoftwareInstance_tryToInvalidateIfDestroyed',
  activate_kw={'tag': tag},
  **{"slapos_item.slap_state": "destroy_requested"}

)

context.activate(after_tag=tag).getId()
