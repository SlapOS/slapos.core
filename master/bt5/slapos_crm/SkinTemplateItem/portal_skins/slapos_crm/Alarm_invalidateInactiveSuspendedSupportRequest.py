portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
      portal_type="Support Request",
      simulation_state=["suspended"],
      method_id='SupportRequest_closeIfInactiveForAMonth',
      activate_kw={'tag': tag}
      )
context.activate(after_tag=tag).getId()
