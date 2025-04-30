data_dict['portal_type'] = 'Compute Node'
compute_node = context.JSONRPCService_getObjectFromData(data_dict)

compute_node.reportComputeNodeBang(comment=data_dict["message"])

return {
  "title": "Bang handled",
  "type": "success"
}
