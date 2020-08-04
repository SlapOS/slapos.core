from Products.ERP5Type.Document import newTempBase

return_list = []
try:
  connection_dict = context.getConnectionXmlAsDict()
except Exception:
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
    d = newTempBase(portal, relative_url)
    d.edit(connection_key=k, connection_value=connection_dict[k])
  return_list.append(d)
return return_list
