# Use a diferent script for the same purpose only to be used for download
response = context.REQUEST.RESPONSE
mime_type = 'application/hal+json'
response.setHeader('Content-Type', mime_type)

return context.SupportRequestModule_getMonitoringOPMLDescriptionList(**kw)
