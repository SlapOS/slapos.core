# Search for Google Login that is activated and run migration scripts

portal = context.getPortalObject()

activate_kw = {}
if tag:
  activate_kw["tag"] = tag

portal.portal_catalog.searchAndActivate(
  portal_type='Google Login',
  validation_state='validated',
  method_id='GoogleLogin_migrateToERP5Login',
  method_kw={'dry_run': dry_run},
  activate_kw=activate_kw
  )

context.portal_alarms.activate(after_tag=tag).getId()
