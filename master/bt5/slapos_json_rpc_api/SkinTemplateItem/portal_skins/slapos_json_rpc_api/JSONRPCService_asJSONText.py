data_dict['portal_type'] = "Software Instance"
doc = context.JSONRPCService_getObjectFromData(data_dict)
return doc.asJSONText()
