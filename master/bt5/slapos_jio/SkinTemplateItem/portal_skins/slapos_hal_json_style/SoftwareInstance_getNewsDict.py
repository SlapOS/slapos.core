from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal_type = context.getPortalType()
if portal_type == "Slave Instance":
  return {
    "user": "SlapOS Master",
    "text": "#nodata is a slave %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_slave": 1
  }

slap_state = context.getSlapState()
if portal_type == "Software Instance" and slap_state == "stop_requested":
  return {
    "user": "SlapOS Master",
    "text": "#nodata is an stopped instance %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_stopped": 1
  }

if portal_type == "Software Instance" and slap_state == "destroy_requested":
  return {
    "user": "SlapOS Master",
    "text": "#nodata is an destroyed instance %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_destroyed": 1
  }

news_dict = context.getAccessStatus()
news_dict["monitor_url"] = context.Base_getStatusMonitorUrl()
return news_dict
