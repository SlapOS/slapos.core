portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
      portal_type="Person", 
      validation_state="validated",
      destination_section_related__portal_type="Payment Transaction",
      destination_section_related__simulation_state="started",
      method_id='Person_checkToCreateRegularisationRequest',
      activate_kw={'tag': tag}
      )
context.activate(after_tag=tag).getId()
