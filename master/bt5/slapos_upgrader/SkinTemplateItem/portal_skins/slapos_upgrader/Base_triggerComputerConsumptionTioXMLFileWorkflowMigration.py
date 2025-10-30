portal = context.getPortalObject()
tag = script.id

portal.portal_catalog.searchAndActivate(
  portal_type="Computer Consumption TioXML File",
  activate_kw={'tag': tag},
  method_id="ComputerConsumptionTioXMLFile_migrateConsumptionDocumentWorkflowHistory",
)
return context.activate(after_tag=tag, priority=4).getId()
