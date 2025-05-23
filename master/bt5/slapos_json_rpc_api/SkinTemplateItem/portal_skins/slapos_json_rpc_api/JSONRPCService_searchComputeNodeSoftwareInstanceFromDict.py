portal_type = "Software Instance"
portal = context.getPortalObject()

slap_state_dict = {
  "stop_requested": "stopped",
  "start_requested": "started",
  "destroy_requested": "destroyed",
}

search_kw = {
  "portal_type": portal_type,
  "validation_state": "validated",
  "select_list": ("title", "reference", "portal_type", "slap_state", "aggregate_reference", "url_string"),
  # XXX Sorting is slow
  "sort_on": [("reference", "ASC")]
}


search_kw["aggregate_parent_reference"] = data_dict["computer_guid"]

# Keep previous SlapTool behaviour
user_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user_value is not None and user_value.getReference() == data_dict["computer_guid"]:
  compute_node = user_value
  compute_node.setAccessStatus(data_dict["computer_guid"])

result_list = [{
  "title": x.title,
  "instance_guid": x.reference,
  "state": slap_state_dict.get(x.slap_state, ""),
  "compute_partition_id": x.aggregate_reference,
  "software_release_uri": x.url_string,
} for x in portal.portal_catalog(**search_kw)]

return {
  "result_list": result_list
}
