portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
    portal_type='Project',
    validation_state='validated',
    method_id='Project_checkMonitoringState',
    activate_kw={'tag': tag}
  )
context.activate(after_tag=tag).getId()
