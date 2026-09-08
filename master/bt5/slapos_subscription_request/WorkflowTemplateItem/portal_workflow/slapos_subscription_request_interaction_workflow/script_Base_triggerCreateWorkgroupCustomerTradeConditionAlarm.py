if state_change['object'].getDestinationSection(portal_type='Workgroup'):
  return state_change['object'].Base_reindexAndSenseAlarm(['slapos_subscription_create_workgroup_customer_trade_condition'])
