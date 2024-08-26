portal = context.getPortalObject()

############################################
# Trigger open order creation for virtual master
############################################
alarm = portal.restrictedTraverse('portal_alarms/slapos_subscription_request_validate_submitted')
alarm.activeSense()

context.activate(after_path=alarm.getPath(), priority=4).Base_triggerFullSiteMigrationToVirtualMasterStep9()
