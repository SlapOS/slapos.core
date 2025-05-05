data_dict['portal_type'] = 'Software Instance Certificate Record'
software_instance = context.JSONRPCService_getObjectFromData(data_dict)

return {
  "key": software_instance.getSslKey(),
  "certificate": software_instance.getSslCertificate()
}
