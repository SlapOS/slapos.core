data_dict['portal_type'] = 'Software Instance'
instance = context.JSONRPCService_getObjectFromData(data_dict)

error_log = data_dict.get("message", "")
instance.setErrorStatus('while instanciating: %s' % error_log[-80:], reindex=1)

return {
  "title": "Error reported",
  "type": "success"
}
