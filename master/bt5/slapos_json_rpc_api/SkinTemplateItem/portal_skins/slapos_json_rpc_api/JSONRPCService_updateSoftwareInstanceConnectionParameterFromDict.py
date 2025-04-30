data_dict['portal_type'] = 'Software Instance'
instance = context.JSONRPCService_getObjectFromData(data_dict)

castToStr = context.Base_castDictToXMLString
connection_xml = castToStr(data_dict["connection_parameter_dict"])
result = "connection parameter not modified as identical"
if not instance.isLastData(value=connection_xml):
  # XXX why not directory checking the current connection_xml from the instance?
  result = "connection parameter updated"
  instance.updateConnection(
    connection_xml=connection_xml,
  )

return {
  "title": result,
  "type": "success"
}
