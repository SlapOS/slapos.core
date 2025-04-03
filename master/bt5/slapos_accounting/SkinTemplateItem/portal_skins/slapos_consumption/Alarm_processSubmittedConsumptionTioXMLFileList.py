portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type="Computer Consumption TioXML File",
  validation_state="submitted",
  method_id='ComputerConsumptionTioXMLFile_generateConsumptionDelivery',
  activity_count=100,
  packet_size=100,
  activate_kw={'tag': tag, 'priority': 5}
)

context.activate(after_tag=tag).getId()
