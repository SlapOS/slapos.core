portal = context.getPortalObject()
alarm_tool = portal.portal_alarms

# Higher than simulable movement priority
PRIORITY = 4

if alarm_tool.isSubscribed() and len(alarm_id_list):
  # No alarm tool is not subscribed, respect this choice and do not activate any alarm

  tag = None
  if must_reindex_context:
    tag = "%s-%s" % (script.id, context.getRelativeUrl())
    context.reindexObject(activate_kw={'tag': tag})

  for alarm_id in alarm_id_list:
    alarm = alarm_tool.restrictedTraverse(alarm_id)
    if alarm.isEnabled():
      # do nothing if the alarm is not enabled

      if tag is not None:
        activate_kw = {}
        activate_kw['activity'] = 'SQLQueue'
        activate_kw['after_tag'] = tag
        # Wait for the previous alarm run to be finished
        context.activate(**activate_kw).Base_reindexAndSenseAlarm([alarm_id],
                                                                  must_reindex_context=False)
      elif alarm.isActive():
        activate_kw = {}
        activate_kw['priority'] = PRIORITY
        activate_kw['after_path_and_method_id'] = (alarm.getPath(), 'getId')
        # Wait for the previous alarm run to be finished
        # call on alarm tool to gather and drop with sqldict
        alarm_tool.activate(**activate_kw).Base_reindexAndSenseAlarm([alarm_id],
                                                                     must_reindex_context=False)
      else:
        # Do not call directly call activeSense, because in case of concurrency,
        # it will trigger the alarm multiple time in parallel
        # Wait for the previous alarm run to be finished
        # wait for the context to be reindexed before activating the alarm
        # ROMAIN: getId is used, because most alarm script ends with an getId activity
        # priority=3, to be executed after all reindex, but also execute simulation _expand
        alarm.activate(priority=PRIORITY).activeSense()
        # Prevent 2 nodes to call activateSense concurrently
        alarm.serialize()
