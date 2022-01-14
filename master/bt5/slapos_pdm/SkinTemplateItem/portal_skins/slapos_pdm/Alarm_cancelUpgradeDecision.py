portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type="Upgrade Decision Line",
  simulation_state=["confirmed", "draft", "planned"],
  method_id = 'UpgradeDecisionLine_cancel',
  activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
