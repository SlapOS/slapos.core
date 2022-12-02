node_id = data_dict.get("node_id", None)

portal = context.getPortalObject()

search_kw = {
  "portal_type": "Hash Document Record",
  "select_list": ("reference", "creation_date"),
  "sort_on": (("creation_date", "DESC"),),
  "limit": 1
}
if node_id:
  search_kw["strict_aggregate_reference"] = node_id

hash_document_list = portal.portal_catalog(**search_kw)

result_list = []
for hash_document in hash_document_list:
  result_list.append({
    "portal_type": "Hash Document Record",
    # Hackish
    "timestamp": hash_document.reference.split("-")[-1],
    "reference": hash_document.reference,
  })
  
import json
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "result_list": result_list,
}, indent=2)
