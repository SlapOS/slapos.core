import json

software_installation = context
url = software_installation.getUrlString()
tag = "%s_%s_inProgress" % (software_installation.getAggregateUid(portal_type="Compute Node"),
                            software_installation.getUrlString())

logError = context.ERP5Site_logApiErrorAndReturn

if "state" in data_dict:
# Change desired state
  state = data_dict["state"]
  if (state == "available"):
    software_installation.requestStart()
  elif (state == "destroyed"):
    software_installation.requestDestroy(activate_kw={'tag': tag})
  else:
    return logError(
      error_name="SOFTWARE-INSTALLATION-WRONG-STATE",
      error_message="State should be available or destroyed, but is %s" % state,
    )

if "reported_state" in data_dict:
  reported_state = data_dict["reported_state"]
  if reported_state == "available":
    software_installation.setAccessStatus('software release %s available' % url, "available")
  elif reported_state == "building":
    software_installation.setBuildingStatus('software release %s' % url, "building")
  elif reported_state == "destroyed":
    if software_installation.getSlapState() != 'destroy_requested':
      return logError(
        error_name="SOFTWARE-INSTALLATION-DESTROY-NOT-REQUESTED",
        error_message="Reported state is destroyed but requested state is not destroyed",
      )
    if context.getPortalObject().portal_workflow.isTransitionPossible(software_installation,
        'invalidate'):
      software_installation.invalidate(
        comment="Software Release destroyed report.")
  else:
    return logError(
      error_name="SOFTWARE-INSTALLATION-WRONG-REPORTED-STATE",
      error_message="Reported state should be available, destroyed or building, but is %s" % state,
    )

if "error_status" in data_dict:
  software_installation.setErrorStatus('while installing %s' % url)

return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "id": software_installation.getRelativeUrl(),
  "date": str(DateTime()),
  "success": "Done"
}, indent=2)
