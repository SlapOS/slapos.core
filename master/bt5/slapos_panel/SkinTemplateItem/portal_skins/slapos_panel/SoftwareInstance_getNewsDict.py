from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal_type = context.getPortalType()
if portal_type == "Slave Instance":
  return {
    "portal_type": context.getPortalType(),
    "reference": context.getReference(),
    "user": "SlapOS Master",
    "text": "#nodata is a slave %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_slave": 1
  }

slap_state = context.getSlapState()
if portal_type == "Software Instance" and slap_state == "stop_requested":
  return {
    "portal_type": context.getPortalType(),
    "reference": context.getReference(),
    "user": "SlapOS Master",
    "text": "#nodata is an stopped instance %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_stopped": 1
  }

if portal_type == "Software Instance" and slap_state == "destroy_requested":
  return {
    "portal_type": context.getPortalType(),
    "reference": context.getReference(),
    "user": "SlapOS Master",
    "text": "#nodata is an destroyed instance %s" % context.getReference(),
    "monitor_url": context.Base_getStatusMonitorUrl(),
    "is_destroyed": 1
  }

news_dict = context.getAccessStatus()
news_dict["monitor_url"] = context.Base_getStatusMonitorUrl()
return news_dict
