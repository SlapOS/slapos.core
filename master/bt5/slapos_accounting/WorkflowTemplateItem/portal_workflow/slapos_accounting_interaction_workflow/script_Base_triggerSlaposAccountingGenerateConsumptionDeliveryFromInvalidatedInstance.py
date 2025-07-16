instance = state_change['object']
instance.setExpirationDate(None)
return instance.Base_reindexAndSenseAlarm(['slapos_accounting_generate_consumption_delivery_for_invalidated_instance'])
