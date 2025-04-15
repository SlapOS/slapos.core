from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class WrongReportedStateError(JsonRpcAPIError):
  type = "SOFTWARE-INSTANCE-WRONG-REPORTED-STATE"
  status = 403

software_instance = context.JSONRPCService_getObjectFromData(data_dict)

if "reported_state" in data_dict:
# Change desired state
  reported_state = data_dict["reported_state"]
  if (reported_state == "bang"):
    software_instance.setErrorStatus('bang called')
    timestamp = str(int(software_instance.getModificationDate()))
    key = "%s_bangstamp" % software_instance.getReference()

    if not software_instance.isLastData(key, timestamp):
      software_instance.bang(bang_tree=True, comment=data_dict.get("status_message", ""))
  else:
    raise WrongReportedStateError("Unexpected Reported State: %s" % reported_state)

return {
  #"$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "reference": software_instance.getReference(),
  "portal_type": "Software Instance",
  "date": DateTime().ISO8601(),
  "success": "Done"
}
