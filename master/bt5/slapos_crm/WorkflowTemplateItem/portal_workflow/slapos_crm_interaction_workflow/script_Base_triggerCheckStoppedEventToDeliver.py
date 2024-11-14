event = state_change['object']
ticket = event.getFollowUpValue()

if ticket is None:
  return

if ticket.getPortalType() == 'Support Request':
  return event.Base_reindexAndSenseAlarm(
    ['slapos_crm_check_stopped_event_from_support_request_to_deliver'])
elif ticket.getPortalType() == 'Regularisation Request':
  return event.Base_reindexAndSenseAlarm(
    ['slapos_crm_check_stopped_event_from_regularisation_request_to_deliver'])
elif ticket.getPortalType() == 'Subscription Request':
  return event.Base_reindexAndSenseAlarm(
    ['slapos_subscription_check_stopped_event_from_subscription_request_to_deliver'])
elif ticket.getPortalType() == 'Upgrade Decision':
  return event.Base_reindexAndSenseAlarm(
    ['slapos_pdm_check_stopped_event_from_upgrade_decision_to_deliver'])
