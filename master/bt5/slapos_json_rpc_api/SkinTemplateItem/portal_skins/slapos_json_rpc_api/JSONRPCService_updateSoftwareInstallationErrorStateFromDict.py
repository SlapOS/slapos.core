data_dict['portal_type'] = 'Software Installation'
software_installation = context.JSONRPCService_getObjectFromData(data_dict)

error_log = data_dict.get("message", "")
software_installation.setErrorStatus('while installing: %s' % error_log, reindex=1)

return {
  "title": "Error reported",
  "type": "success"
}
