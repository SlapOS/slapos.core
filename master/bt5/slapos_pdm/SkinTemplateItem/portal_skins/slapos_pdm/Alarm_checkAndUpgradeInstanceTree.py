portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  validation_state = 'validated',
  method_id = 'InstanceTree_createUpgradeDecision',
  activate_kw = {'tag':tag},
  **{"slapos_item.slap_state": ['start_requested', 'stop_requested']}
)

context.activate(after_tag=tag).getId()
