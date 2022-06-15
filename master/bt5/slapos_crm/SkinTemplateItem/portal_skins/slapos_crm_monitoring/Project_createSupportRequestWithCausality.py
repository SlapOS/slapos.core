portal = context.getPortalObject()
project = context

causality_value = portal.restrictedTraverse(causality)

if causality_value.Base_getSupportRequestInProgress(title=title) is not None:
  return

destination_decision_value = portal.restrictedTraverse(destination_decision)

return destination_decision_value.Entity_createTicketFromTradeCondition(
  portal.service_module.slapos_crm_monitoring.getRelativeUrl(),
  title,
  text_content,
  source_project=project.getRelativeUrl(),
  causality=causality
)
