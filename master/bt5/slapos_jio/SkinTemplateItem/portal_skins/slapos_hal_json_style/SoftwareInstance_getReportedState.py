from DateTime import DateTime
import json

slap_state = context.getSlapState()

_translate = context.Base_translateString

NOT_ALLOCATED = _translate("Searching Partition")
STARTING = _translate("Starting")
STARTED = _translate("Started")
STOPPING = _translate("Stopping")
STOPPED = _translate("Stopped")
DESTROYING = _translate("Destroying")
DESTROYED = _translate("Destroyed")
FAILING_STOP = _translate("Failing to stop")
FAILING_START = _translate("Failing to start")
UNKNOWN = _translate("Waiting contact from the instance")

computer_partition = context.getAggregateValue(portal_type="Computer Partition")
if computer_partition is not None:
  memcached_dict = context.Base_getSlapToolMemcachedDict()
  try:
    d = memcached_dict[context.getReference()]
  except KeyError:
    return _translate(context.getSlapStateTitle())

  d = json.loads(d)
  result = d['text']
  reported_state = d.get("state", "")
  if reported_state == "":
    return UNKNOWN

  if slap_state == "destroy_requested":
    return DESTROYING


  if reported_state == "stopped":
    if slap_state == "start_requested":
      if result.startswith('#error '):
        return FAILING_START
      return STARTING

    elif slap_state == "stop_requested":
      return STOPPED

  elif reported_state == "started":
    if slap_state == "start_requested":
      return STARTED
    elif slap_state == "stop_requested":
      if result.startswith('#error '):
        return FAILING_STOP
      return STOPPING

  raise ValueError("%s %s %s Unknown State" % (context.getRelativeUrl(), result, slap_state))


if slap_state == "destroy_requested":
  return DESTROYED

return NOT_ALLOCATED
