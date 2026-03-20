assignment_request = state_change['object']

# Only trigger if person enters a workgroup.
if assignment_request.getDestination(portal_type="Workgroup") is not None:
  return assignment_request.Base_reindexAndSenseAlarm(['slapos_handle_assignment_request_to_suspend_alarm'])
