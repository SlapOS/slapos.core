from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class WrongReportedStateError(JsonRpcAPIError):
  type = "SOFTWARE-INSTANCE-WRONG-REPORTED-STATE"
  status = 403

data_dict['portal_type'] = 'Software Instance'
software_instance = context.JSONRPCService_getObjectFromData(data_dict)

# Change desired state
reported_state = data_dict["reported_state"]
if (reported_state == "started"):
  software_instance.setAccessStatus(
    'Instance correctly started', "started", reindex=1)
elif (reported_state == "stopped"):
  software_instance.setAccessStatus(
    'Instance correctly stopped', "stopped", reindex=1)
elif (reported_state == "destroyed"):
  if software_instance.getSlapState() == 'destroy_requested':
    # remove certificate from SI
    software_instance.revokeCertificate()
    if software_instance.getValidationState() == 'validated':
      software_instance.invalidate()
else:
  raise WrongReportedStateError("Unexpected Reported State: %s" % reported_state)

return {
  "title": "State reported",
  "type": "success"
}
