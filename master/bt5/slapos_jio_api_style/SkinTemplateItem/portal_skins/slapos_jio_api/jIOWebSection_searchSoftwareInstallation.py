# Hardcoded
limit = 1000
web_section = context.getWebSectionValue()
web_section = web_section.getRelativeUrl() if web_section else context.REQUEST.get("web_section_relative_url", None)

search_kw = {
  "portal_type": "Software Installation",
  "validation_state": "validated",
  "jio_api_revision.web_section": web_section,
  "select_list": ("aggregate_reference", "url_string", "slap_state", "portal_type", "slap_date", "jio_api_revision.revision"),
  "sort_on": ("jio_api_revision.revision", "ASC"),
  "limit": limit,
}

if "software_release_uri" in data_dict:
  import urllib
  search_kw["url_string"] = urllib.unquote(data_dict["software_release_uri"])
if "compute_node_id" in data_dict:
  search_kw["strict_aggregate_reference"] = data_dict["compute_node_id"]
if "from_api_revision" in data_dict:
  search_kw["jio_api_revision.revision"] = "> %s" % data_dict["from_api_revision"]

result_list = [{
  "get_parameters": {
    "software_release_uri": x.url_string,
    "compute_node_id": x.aggregate_reference,
    "portal_type": x.portal_type,
  },
  "software_release_uri": x.url_string,
  "compute_node_id": x.aggregate_reference,
  "state": "available" if x.slap_state == "start_requested" else "destroyed",
  "api_revision": x.revision,
  "portal_type": x.portal_type,
  "processing_timestamp": int(x.slap_date),
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
