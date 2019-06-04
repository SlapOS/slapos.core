portal= context.getPortalObject()

instance_list = []

for support_request in portal.portal_catalog(
  portal_type="Support Request",
  simulation_state=["validated", "suspended"]):
  instance_list.extend(support_request.SupportRequest_getInstanceMessageList())

return instance_list
