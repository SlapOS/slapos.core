portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='Workgroup_validateIfSubmitted',
  method_kw={'activate_kw': {'tag': tag}},
  portal_type=["Workgroup"],
  validation_state='submitted',
  destination__uid='%',
  packet_size=1, # Separate calls to many transactions
  activate_kw={'tag': tag, 'priority': 2}
)

context.activate(after_tag=tag).getId()
