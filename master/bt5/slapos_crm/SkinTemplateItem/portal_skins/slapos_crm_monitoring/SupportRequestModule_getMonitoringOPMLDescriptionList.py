from json import dumps
import base64

def getCredentialFromUrl(parameter_string):
  username = ''
  password = ''
  if 'username' in parameter_string and \
     'password' in parameter_string:
    param_list = parameter_string.split('&')
    for param in param_list:
      key, value = param.split('=')
      if key == 'username':
        username = value
      elif key == 'password':
        password = value

  return (username, password,)

def getMonitorUrlFromUrlString(parameter_string):
  if 'url=' in parameter_string:
    param_list = parameter_string.split('&')
    for param in param_list:
      key, value = param.split('=')
      if key == 'url':
        return value

monitor_instance_list = []
monitor_url_temp_object_list = context.SupportRequestModule_getMonitoringUrlList()

for temp_object in monitor_url_temp_object_list:
  monitor_url = getMonitorUrlFromUrlString(temp_object.monitor_url)
  username, password = getCredentialFromUrl(temp_object.monitor_url)

  if monitor_url is not None:
    monitor_instance_list.append(dict(
        basic_login=base64.b64encode('%s:%s' % (username, password)),
        url=monitor_url,
        title=temp_object.title,
        active=True
      ))


monitor_parameter_dict = {"opml_description_list": monitor_instance_list}
return dumps(monitor_parameter_dict)
