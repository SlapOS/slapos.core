portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
      portal_type="Regularisation Request", 
      simulation_state=["suspended", "validated"],
      method_id='RegularisationRequest_invalidateIfPersonBalanceIsOk',
      activate_kw={'tag': tag}
      )
context.activate(after_tag=tag).getId()
