portal = context.getPortalObject()
project = context

causality_value = portal.restrictedTraverse(causality)

if portal.portal_catalog.getResultValue(
  portal_type='Support Request',
  title={'query': title, 'key': 'ExactMatch'},
  simulation_state=["validated", "submitted", "suspended"],
  causality__uid=causality_value.getUid(),
) is not None:
  return

destination_decision_value = portal.restrictedTraverse(destination_decision)

return destination_decision_value.Entity_createTicketFromTradeCondition(
  portal.service_module.slapos_crm_monitoring.getRelativeUrl(),
  title,
  text_content,
  source_project=project.getRelativeUrl(),
  causality=causality
)
