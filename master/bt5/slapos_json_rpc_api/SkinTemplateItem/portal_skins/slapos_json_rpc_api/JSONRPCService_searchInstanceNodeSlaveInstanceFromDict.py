from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

portal_type = "Slave Instance"
portal = context.getPortalObject()

class HostInstanceNotFoundError(JsonRpcAPIError):
  type = "HOST-INSTANCE-NOT-FOUND"
  status = 403

slap_state_dict = {
  "stop_requested": "stopped",
  "start_requested": "started",
  "destroy_requested": "destroyed",
}

search_kw = {
  "portal_type": portal_type,
  "validation_state": "validated",
  "select_list": ("title", "reference", "source_reference", "portal_type", "slap_state", "aggregate_reference"),
  "sort_on": [("reference", "ASC")]
}

host_instance_list = portal.portal_catalog(
  portal_type="Software Instance",
  reference=data_dict["reference"],
  validation_state="validated",
  limit=2
)
if len(host_instance_list) != 1:
  raise HostInstanceNotFoundError("No matching instances with the provided reference has been found")
else:
  search_kw["strict_aggregate_uid"] = host_instance_list[0].getObject().getAggregateUid()

result_list = [{
  "title": x.title,
  "reference": x.reference,
  "portal_type": "Slave Instance",
  "software_type": x.source_reference,
  "state": slap_state_dict.get(x.slap_state, ""),
  "parameters": x.getInstanceXmlAsDict(),
  #"processing_timestamp": x.getSlapTimestamp(),
  "compute_partition_id": x.aggregate_reference,
} for x in portal.portal_catalog(**search_kw)]

return {
  "result_list": result_list
}
