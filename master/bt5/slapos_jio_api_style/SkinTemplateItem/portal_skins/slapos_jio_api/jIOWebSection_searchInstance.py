portal_type = data_dict["portal_type"]
portal = context.getPortalObject()

reverse_slap_state_dict = {
  "stopped": "stop_requested",
  "started": "start_requested",
  "destroyed": "destroy_requested",
}

slap_state_dict = {
  "stop_requested": "stopped",
  "start_requested": "started",
  "destroy_requested": "destroyed",
}

if portal_type == "Software Instance":
  search_kw = {
    "portal_type": "Software Instance",
    "validation_state": "validated",
    "select_list": ("title", "reference", "portal_type", "slap_state", "aggregate_reference", "url_string")
  }

  if "title" in data_dict:
    search_kw["title"] = data_dict["title"]
  if "compute_node_id" in data_dict:
    search_kw["aggregate_parent_reference"] = data_dict["compute_node_id"]
  if "compute_partition_id" in data_dict:
    search_kw["aggregate_reference"] = data_dict["compute_partition_id"]
  if "root_instance_title" in data_dict:
    search_kw["strict_specialise_title"] = data_dict["root_instance_title"]
  if "state" in data_dict:
    search_kw["slap_state"] = reverse_slap_state_dict.get(data_dict["state"], "")

  result_list = [{
    "title": x.title,
    "reference": x.reference,
    "portal_type": x.portal_type,
    "state": slap_state_dict.get(x.slap_state, ""),
    "compute_partition_id": x.aggregate_reference,
    "software_release_uri": x.url_string,
  } for x in portal.portal_catalog(**search_kw)]

elif portal_type == "Shared Instance":
  search_kw = {
    "portal_type": "Slave Instance",
    "validation_state": "validated",
    "select_list": ("title", "reference", "portal_type", "slap_state", "aggregate_reference")
  }
  if "host_instance_reference" in data_dict:
    host_instance_list = portal.portal_catalog(
      portal_type="Software Instance",
      reference=data_dict["host_instance_reference"],
      validation_state="validated",
    )
    if len(host_instance_list) != 1:
      return portal.ERP5Site_logApiErrorAndReturn(
        error_name="HOST-INSTANCE-NOT-FOUND",
        error_message="No matching instances with the provided reference has been found",
        error_code=404
      )
    search_kw["strict_aggregate_uid"] = host_instance_list[0].getObject().getAggregateUid()
  if "root_instance_title" in data_dict:
    search_kw["strict_specialise_title"] = data_dict["root_instance_title"]
  if "state" in data_dict:
    search_kw["slap_state"] = reverse_slap_state_dict.get(data_dict["state"], "")
  result_list = [{
    "title": x.title,
    "reference": x.reference,
    "portal_type": "Shared Instance",
    "state": slap_state_dict.get(x.slap_state, ""),
    "compute_partition_id": x.aggregate_reference,
    # Slave Instance don't have url_string cataloged. Selecting it return 0 result each time
    #"software_release_uri": x.url_string,
  } for x in portal.portal_catalog(**search_kw)]

else:
  return portal.ERP5Site_logApiErrorAndReturn(
    error_name="UNREACHABLE",
    error_message="You Reached code that was not recheable",
  )

import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list
}, indent=2)
