data_dict['portal_type'] = 'Compute Node'
compute_node = context.JSONRPCService_getObjectFromData(data_dict)

compute_node.revokeCertificate()

return {
  "title": "Certificate removed",
  "type": "success"
}
