search_kw = {
  "portal_type": "Software Instance",
  "validation_state": "validated",
  "select_list": ("title", "reference", "portal_type")
}

if "title" in data_dict:
  search_kw["title"] = data_dict["title"]
if "compute_node_id" in data_dict:
  search_kw["aggregate_parent_reference"] = data_dict["compute_node_id"]
if "root_instante_title" in data_dict:
  search_kw["strict_specialise_title"] = data_dict["root_instante_title"]

result_list = [{
  "title": x.title,
  "reference": x.reference,
  "portal_type": x.portal_type,
} for x in context.getPortalObject().portal_catalog(**search_kw)]
import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list
}, indent=2)
