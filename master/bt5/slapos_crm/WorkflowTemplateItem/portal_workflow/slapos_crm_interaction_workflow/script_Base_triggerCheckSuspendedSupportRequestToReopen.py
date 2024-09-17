event = state_change['object']
support_request = event.getFollowUpValue()
if (support_request is not None) and (support_request.getSimulationState() == 'suspended'):
  return state_change['object'].Base_reindexAndSenseAlarm(['slapos_crm_check_suspended_support_request_to_reopen'])
