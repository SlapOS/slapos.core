data_dict['portal_type'] = 'Compute Node'
compute_node = context.JSONRPCService_getObjectFromData(data_dict)

compute_node.generateCertificate()

request = context.REQUEST
return {
  "key": request.get('compute_node_key'),
  "certificate": request.get('compute_node_certificate')
}
