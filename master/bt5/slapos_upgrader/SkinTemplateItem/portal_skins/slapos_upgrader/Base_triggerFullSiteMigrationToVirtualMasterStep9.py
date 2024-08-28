portal = context.getPortalObject()
alarm_tool = portal.portal_alarms

############################################
# Trigger open order creation for all services
############################################
alarm_tool.subscribe()
alarm = portal.restrictedTraverse('portal_alarms/slapos_subscription_request_create_from_orphaned_item')
alarm.activeSense()

context.activate(after_path=alarm.getPath(), priority=4).getId()
