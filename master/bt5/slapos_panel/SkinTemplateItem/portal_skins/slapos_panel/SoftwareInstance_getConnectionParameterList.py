from Products.ERP5Type.Document import newTempBase
from Products.ERP5Type.Utils import unicode2str

import json

return_list = []
try:
  connection_dict = context.getConnectionXmlAsDict()
except Exception:
  return return_list

if connection_dict is None:
  return return_list

if connection_dict.keys() == ["_"]:
  json_connection_dict = json.loads(connection_dict["_"])
  if isinstance(json_connection_dict, dict): 
    connection_dict = json_connection_dict

portal = context.getPortalObject()
if relative_url == None:
  relative_url = context.getRelativeUrl()

for k in sorted(connection_dict):
  if raw:
    d = {"connection_key": k, "connection_value": unicode2str(connection_dict[k])}
  else:
    d = newTempBase(portal, relative_url)
    d.edit(connection_key=k, connection_value=unicode2str(connection_dict[k]))
  return_list.append(d)
return return_list
