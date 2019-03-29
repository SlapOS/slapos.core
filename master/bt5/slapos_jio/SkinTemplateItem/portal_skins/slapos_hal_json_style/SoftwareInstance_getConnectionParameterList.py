from Products.ERP5Type.Document import newTempDocument

return_list = []
try:
  connection_dict = context.getConnectionXmlAsDict()
except:
  return return_list

if connection_dict is None:
  return return_list

portal = context.getPortalObject()
if relative_url == None:
  relative_url = context.getRelativeUrl()

for k in sorted(connection_dict):
  if raw:
    d = {"connection_key": k, "connection_value": connection_dict[k]}
  else:
    d = newTempDocument(portal, relative_url)
    d.edit(connection_key=k, connection_value=connection_dict[k])
  return_list.append(d)
return return_list
