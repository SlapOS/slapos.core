search_kw = {
  "portal_type": "Software Installation",
  "validation_state": "validated",
  "select_list": ("aggregate_reference", "url_string", "slap_state", "portal_type"),
}

if "software_release_uri" in data_dict:
  search_kw["url_string"] = data_dict["software_release_uri"]
if "compute_node_id" in data_dict:
  search_kw["strict_aggregate_reference"] = data_dict["compute_node_id"]

result_list = [{
  "software_release_uri": x.url_string,
  "compute_node_id": x.aggregate_reference,
  "state": x.slap_state,
  "portal_type": x.portal_type,
} for x in context.getPortalObject().portal_catalog(**search_kw)]

import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list
}, indent=2)
