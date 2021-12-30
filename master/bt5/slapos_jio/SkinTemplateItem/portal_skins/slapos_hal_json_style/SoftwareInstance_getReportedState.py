from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from DateTime import DateTime
slap_state = context.getSlapState()
_translate = context.Base_translateString

NOT_ALLOCATED = _translate("Searching for partition")
STARTING = _translate("Starting")
STARTED = _translate("Started")
STOPPING = _translate("Stopping")
STOPPED = _translate("Stopped")
DESTROYING = _translate("Destroying")
DESTROYED = _translate("Destroyed")
FAILING_STOP = _translate("Failing to stop")
FAILING_START = _translate("Failing to start")
UNKNOWN = _translate("Waiting contact from the instance")

compute_partition = context.getAggregateValue(portal_type="Compute Partition")
if compute_partition is not None:
  instance = context
  if instance.getPortalType() == "Slave Instance":
    instance = compute_partition.getAggregateRelatedValue(portal_type="Software Instance")

  d = instance.getAccessStatus()
  if d.get("no_data") == 1:
    return _translate(instance.getSlapStateTitle())

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

  raise ValueError("%s %s %s Unknown State" % (instance.getRelativeUrl(), result, slap_state))


if slap_state == "destroy_requested":
  return DESTROYED

return NOT_ALLOCATED
