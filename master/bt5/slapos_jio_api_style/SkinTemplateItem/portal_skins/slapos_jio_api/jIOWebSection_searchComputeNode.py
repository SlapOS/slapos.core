search_kw = {
  "portal_type": "Compute Node",
  "validation_state": "validated",
  "select_list": ("title", "reference", "portal_type"),
}

if "title" in data_dict:
  search_kw["title"] = data_dict["title"]
if "compute_node_id" in data_dict:
  search_kw["reference"] = data_dict["compute_node_id"]

result_list = [{
  "title": x.title,
  "compute_node_id": x.reference,
  "portal_type": x.portal_type,
} for x in context.getPortalObject().portal_catalog(**search_kw)]

import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list
}, indent=2)
