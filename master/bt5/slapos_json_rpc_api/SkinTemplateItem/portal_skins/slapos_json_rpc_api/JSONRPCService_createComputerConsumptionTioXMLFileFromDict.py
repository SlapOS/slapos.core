from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError

class InvalidTioXMLError(JsonRpcAPIError):
  type = "INVALIDATE_TIOXML"
  status = 400

data_dict['portal_type'] = 'Compute Node'
compute_node = context.JSONRPCService_getObjectFromData(data_dict)

source_reference = compute_node.ComputeNode_validateTioXMLAndExtractReference(data_dict['tioxml'])
if source_reference is None:
  raise InvalidTioXMLError("The tioxml does not validate the xsd")

compute_node.ComputeNode_reportComputeNodeConsumption(
  source_reference,
  data_dict['tioxml']
)

return {
  "title": "Usage reported",
  "type": "success"
}
