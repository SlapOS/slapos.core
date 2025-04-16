from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

software_installation = context.JSONRPCService_getObjectFromData(data_dict)

class WrongReportedStateError(JsonRpcAPIError):
  type = "SOFTWARE-INSTALLATION-WRONG-REPORTED-STATE"
  status = 403

class DestroyNotRequestedError(JsonRpcAPIError):
  type = "SOFTWARE-INSTALLATION-DESTROY-NOT-REQUESTED"
  status = 403

url = software_installation.getUrlString()

if "reported_state" in data_dict:
  reported_state = data_dict["reported_state"]
  if reported_state == "available":
    software_installation.setAccessStatus('software release %s available' % url, "available")
  elif reported_state == "building":
    software_installation.setBuildingStatus('software release %s' % url, "building")
  elif reported_state == "destroyed":
    if software_installation.getSlapState() != 'destroy_requested':
      raise DestroyNotRequestedError("Reported state is destroyed but requested state is not destroyed")

    if context.getPortalObject().portal_workflow.isTransitionPossible(software_installation,
        'invalidate'):
      software_installation.invalidate(
        comment="Software Release destroyed report.")
  else:
    raise WrongReportedStateError("Reported state should be available, destroyed or building, but is %s" % reported_state)

return {
  # "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "software_release_uri": software_installation.getUrlString(),
  "compute_node_id": software_installation.getAggregateReference(),
  "date": DateTime().ISO8601(),
  "portal_type": "Software Installation",
  "success": "Done"
}
