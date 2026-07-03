assignment_request = state_change['object']

# Only trigger if person assignment w/o workgroup is invalidated.
if assignment_request.getDestination(portal_type="Workgroup") is None:
  return assignment_request.Base_reindexAndSenseAlarm(['slapos_handle_auto_subscription_request_claim_alarm'])
