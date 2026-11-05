context.getPortalObject().portal_catalog.searchAndActivate(
  method_id="Base_checkStoredBrokenState",
  activate_kw={"tag": tag})

context.activate(after_tag=tag).getId()
