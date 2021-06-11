news_dict = {"instance" : []}

if context.getSlapState() == 'stop_requested':
  news_dict["is_stopped"] = 1
elif context.getSlapState() == 'destroy_requested':
  news_dict["is_destroyed"] = 1
elif context.getRootSlave():
  news_dict["is_slave"] = 1
else:
  news_dict["instance"] = [instance.SoftwareInstance_getNewsDict() for instance in context.getSpecialiseRelatedValueList(portal_type="Software Instance")]

return news_dict
