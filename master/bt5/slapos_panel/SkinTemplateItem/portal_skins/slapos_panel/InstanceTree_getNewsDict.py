news_dict = {
  "portal_type": context.getPortalType(),
  "reference": context.getReference(),
  "title": context.getTitle(),
  "monitor_url": context.Base_getStatusMonitorUrl(),
  "instance" : []}

if context.getSlapState() == 'stop_requested':
  news_dict["is_stopped"] = 1
elif context.getSlapState() == 'destroy_requested':
  news_dict["is_destroyed"] = 1
elif context.getRootSlave():
  news_dict["is_slave"] = 1
else:
  news_dict["instance"] = [instance.SoftwareInstance_getNewsDict() for instance in context.getSpecialiseRelatedValueList(checked_permission='View', portal_type="Software Instance")]
  
return news_dict
