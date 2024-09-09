def getCredentialFromUrl(url_string):
  username = password = url = ''
  param_list = url_string.split('#')
  if len(param_list) == 2:
    param_list = param_list[1].split('&')
    for param in param_list:
      key, value = param.split('=')
      if key == 'url':
        url = value
      elif key == 'username':
        username = value
      elif key == 'password':
        password = value
  return (url, username, password,)

instance_tree = context

if instance_tree.getSlapState() == 'destroy_requested':
  return {}

instance = instance_tree.getSuccessorValue()
if instance is None or instance.getSlapState() == 'destroy_requested':
  return {}

parameter_dict = instance.getConnectionXmlAsDict()

if parameter_dict.keys() == ["_"]:
  import json
  json_connection_dict = json.loads(parameter_dict["_"])
  if isinstance(json_connection_dict, dict):
    parameter_dict = json_connection_dict

url_string = parameter_dict.get('monitor-setup-url', '')
if url_string:
  if 'monitor-user' in parameter_dict and \
      'monitor-password' in parameter_dict and \
      'monitor-base-url' in parameter_dict:
    username = parameter_dict.get('monitor-user')
    password = parameter_dict.get('monitor-password')
    url = parameter_dict.get('monitor-base-url') + '/public/feeds'
  else:
    url, username, password = getCredentialFromUrl(url_string)
else:
  return {}

return {
  'username': username,
  'password': password,
  'url': url
  }
