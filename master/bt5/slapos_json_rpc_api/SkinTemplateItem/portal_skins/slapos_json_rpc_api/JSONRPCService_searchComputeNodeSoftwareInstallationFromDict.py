search_kw = {
  "portal_type": "Software Installation",
  "validation_state": "validated",
  "select_list": ("url_string", "slap_state"),
  'sort_on': [('reference', 'ASC')],
}

search_kw["strict_aggregate_reference"] = data_dict["computer_guid"]
# Keep previous SlapTool behaviour
portal = context.getPortalObject()
user_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user_value is not None and user_value.getReference() == data_dict["computer_guid"]:
  compute_node = user_value
  compute_node.setAccessStatus(data_dict["computer_guid"])

result_list = [{
  "software_release_uri": x.url_string,
  "state": "available" if x.slap_state == "start_requested" else "destroyed"
} for x in portal.portal_catalog(**search_kw)]

return {
  "result_list": result_list
}
