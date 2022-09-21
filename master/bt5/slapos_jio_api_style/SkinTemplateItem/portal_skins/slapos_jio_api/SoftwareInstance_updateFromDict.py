import json

software_instance = context

logError = context.ERP5Site_logApiErrorAndReturn

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
    return logError(
      error_name="SOFTWARE-INSTANCE-WRONG-REPORTED-STATE",
      error_message="Unexcepected Reported State: %s" % reported_state,
    )

if "requested_instance_list" in data_dict:
  software_instance.updateRequestedInstanceList(data_dict["requested_instance_list"])

if "title" in data_dict and data_dict["title"] != software_instance.getTitle():
  software_instance.rename(
    new_name=data_dict["title"],
    comment="Rename %s into %s" % (software_instance.getTitle(), data_dict["title"])
  )

return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "reference": software_instance.getReference(),
  "portal_type": "Software Instance",
  "date": DateTime().HTML4(),
  "success": "Done"
}, indent=2)
