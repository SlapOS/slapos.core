from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class RequestFailsError(JsonRpcAPIError):
  type = "SUPPLY-FAILED"
  status = 403

compute_node = context.jIOWebSection_getObjectFromData({
  'portal_type': 'Compute Node',
  'compute_node_id': data_dict['compute_node_id']
})

compute_node.requestSoftwareRelease(
  software_release_url=data_dict["software_release_uri"],
  state=data_dict.get("state", "available"),
)

software_installation_url = context.REQUEST.get("software_installation_url")
if not software_installation_url:
  raise RequestFailsError("Installation request for '%s' with state '%s' on '%s' failed" % (
    data_dict["software_release_uri"],
    data_dict.get("state", "available"),
    data_dict["compute_node_id"]
  ))

return
