from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class WrongReportedStateError(JsonRpcAPIError):
  type = "SOFTWARE-INSTANCE-WRONG-REPORTED-STATE"
  status = 403

software_instance = context.JSONRPCService_getObjectFromData(data_dict)

castToStr = context.Base_castDictToXMLString
if "connection_parameters" in data_dict:
  connection_xml = castToStr(data_dict["connection_parameters"])
  if not software_instance.isLastData(value=connection_xml):
    software_instance.updateConnection(
      connection_xml=connection_xml,
    )

if "reported_state" in data_dict:
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
  elif (reported_state == "bang"):
    software_instance.setErrorStatus('bang called')
    timestamp = str(int(software_instance.getModificationDate()))
    key = "%s_bangstamp" % software_instance.getReference()

    if not software_instance.isLastData(key, timestamp):
      software_instance.bang(bang_tree=True, comment=data_dict.get("status_message", ""))
  elif (reported_state == "error"):
    error_log = data_dict.get("status_message", "")
    software_instance.setErrorStatus('while instanciating: %s' % error_log[-80:], reindex=1)
  else:
    raise WrongReportedStateError("Unexcepected Reported State: %s" % reported_state)

if "title" in data_dict and data_dict["title"] != software_instance.getTitle():
  software_instance.rename(
    new_name=data_dict["title"],
    comment="Rename %s into %s" % (software_instance.getTitle(), data_dict["title"])
  )

return {
  #"$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "reference": software_instance.getReference(),
  "portal_type": "Software Instance",
  "date": DateTime().ISO8601(),
  "success": "Done"
}
