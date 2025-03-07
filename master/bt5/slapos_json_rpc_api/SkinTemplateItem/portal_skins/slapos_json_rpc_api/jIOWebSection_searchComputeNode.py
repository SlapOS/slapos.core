# Hardcoded
limit = 1000
web_section = context.getWebSectionValue()
web_section = web_section.getRelativeUrl() if web_section else context.REQUEST.get("web_section_relative_url", None)

search_kw = {
  "portal_type": "Compute Node",
  "validation_state": "validated",
  "select_list": ("title", "reference", "portal_type", "jio_api_revision.revision"),
  "jio_api_revision.web_section": web_section,
  "sort_on": ("jio_api_revision.revision", "ASC"),
  "limit": limit,
}

if "title" in data_dict:
  search_kw["title"] = data_dict["title"]
if "compute_node_id" in data_dict:
  search_kw["reference"] = data_dict["compute_node_id"]
if "from_api_revision" in data_dict:
  search_kw["jio_api_revision.revision"] = "> %s" % data_dict["from_api_revision"]

result_list = [{
  "title": x.title,
  "compute_node_id": x.reference,
  "portal_type": x.portal_type,
  "api_revision": x.revision,
  "get_parameters": {
    "compute_node_id": x.reference,
    "portal_type": x.portal_type,
  }
} for x in context.getPortalObject().portal_catalog(**search_kw)]

if result_list:
  data_dict["from_api_revision"] = result_list[-1]["api_revision"]
import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list,
  "next_page_request": data_dict,
  "current_page_full": len(result_list) == limit,
}, indent=2)
