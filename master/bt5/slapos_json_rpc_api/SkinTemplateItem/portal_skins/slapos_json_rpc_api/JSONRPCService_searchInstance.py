from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

portal_type = data_dict["portal_type"]
portal = context.getPortalObject()

# Hardcoded
limit = 1000

class HostInstanceNotFoundError(JsonRpcAPIError):
  type = "HOST-INSTANCE-NOT-FOUND"
  status = 403

web_section = context.getWebSectionValue()
web_section = web_section.getRelativeUrl() if web_section else context.REQUEST.get("web_section_relative_url", None)

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
    #"jio_api_revision.web_section": web_section,
    "select_list": ("title", "reference", "portal_type", "slap_state", "aggregate_reference", "url_string"),#, "jio_api_revision.revision"),
    #"sort_on": ("jio_api_revision.revision", "ASC"),
    # XXX Sorting is slow
    "sort_on": [("reference", "ASC")],
    "limit": limit
  }

  if "title" in data_dict:
    search_kw["title"] = data_dict["title"]
  if "compute_node_id" in data_dict:
    search_kw["aggregate_parent_reference"] = data_dict["compute_node_id"]

    # Keep previous SlapTool behaviour
    user_value = portal.portal_membership.getAuthenticatedMember().getUserValue()
    if user_value is not None and user_value.getReference() == data_dict["compute_node_id"]:
      compute_node = user_value
      compute_node.setAccessStatus(data_dict["compute_node_id"])

  if "compute_partition_id" in data_dict:
    search_kw["aggregate_reference"] = data_dict["compute_partition_id"]
  if "root_instance_title" in data_dict:
    search_kw["strict_specialise_title"] = data_dict["root_instance_title"]
  if "state" in data_dict:
    search_kw["slap_state"] = reverse_slap_state_dict.get(data_dict["state"], "")
  if "from_api_revision" in data_dict:
    search_kw["jio_api_revision.revision"] = "> %s" % data_dict["from_api_revision"]
  result_list = [{
    "title": x.title,
    "reference": x.reference,
    "portal_type": x.portal_type,
    "state": slap_state_dict.get(x.slap_state, ""),
    "compute_partition_id": x.aggregate_reference,
    "software_release_uri": x.url_string,
    #"api_revision": x.revision,
    "get_parameters": {
      "portal_type": x.portal_type,
      "reference": x.reference,
    },
  } for x in portal.portal_catalog(**search_kw)]

elif portal_type == "Slave Instance":
  search_kw = {
    "portal_type": "Slave Instance",
    "validation_state": "validated",
    # "jio_api_revision.web_section": web_section,
    "select_list": ("title", "reference", "portal_type", "slap_state", "aggregate_reference"),#, "jio_api_revision.revision"),
    # "sort_on": ("jio_api_revision.revision", "ASC"),
    "sort_on": [("reference", "ASC")],
    "limit": limit
  }
  if "host_instance_reference" in data_dict:
    host_instance_list = portal.portal_catalog(
      portal_type="Software Instance",
      reference=data_dict["host_instance_reference"],
      validation_state="validated",
    )
    if len(host_instance_list) != 1:
      raise HostInstanceNotFoundError("No matching instances with the provided reference has been found")

    search_kw["strict_aggregate_uid"] = host_instance_list[0].getObject().getAggregateUid()
  if "root_instance_title" in data_dict:
    search_kw["strict_specialise_title"] = data_dict["root_instance_title"]
  if "state" in data_dict:
    search_kw["slap_state"] = reverse_slap_state_dict.get(data_dict["state"], "")
  if "from_api_revision" in data_dict:
    search_kw["jio_api_revision.revision"] = "> %s" % data_dict["from_api_revision"]

  result_list = [{
    "title": x.title,
    "reference": x.reference,
    "portal_type": "Slave Instance",
    "state": slap_state_dict.get(x.slap_state, ""),
    "compute_partition_id": x.aggregate_reference,
    #"api_revision": x.revision,
    "get_parameters": {
      "portal_type": "Slave Instance",
      "reference": x.reference,
    },
    # Slave Instance don't have url_string cataloged. Selecting it return 0 result each time
    #"software_release_uri": x.url_string,
  } for x in portal.portal_catalog(**search_kw)]

else:
  raise NotImplementedError('Unsupported portal type: %s' % portal_type)


#if result_list:
#  data_dict["from_api_revision"] = result_list[-1]["api_revision"]

return {
  # "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list,
  "next_page_request": data_dict,
  "current_page_full": len(result_list) == limit,
}
