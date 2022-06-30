portal_type = data_dict["portal_type"]
portal = context.getPortalObject()

if portal_type == "Software Instance":
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
  } for x in portal.portal_catalog(**search_kw)]

elif portal_type == "Shared Instance":
  search_kw = {
    "portal_type": "Slave Instance",
    "validation_state": "validated",
    "select_list": ("title", "reference", "portal_type")
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
  if "root_instante_title" in data_dict:
    search_kw["strict_specialise_title"] = data_dict["root_instante_title"]
  #return portal.portal_catalog(src__=1, **search_kw)
  result_list = [{
    "title": x.title,
    "reference": x.reference,
    "portal_type": x.portal_type,
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
