data_dict['portal_type'] = 'Compute Node'
compute_node = context.JSONRPCService_getObjectFromData(data_dict)

return compute_node.getAccessStatus()
