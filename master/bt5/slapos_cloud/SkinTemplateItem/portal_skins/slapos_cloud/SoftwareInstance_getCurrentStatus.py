"""Dirty script to return Software Instance state"""
state = context.getSlapState()
has_partition = context.getAggregate(portal_type="Compute Partition")
result = 'Unable to calculate the status...'
if has_partition:
  d = context.getAccessStatus()
  if d.get("no_data") == 1:
    result = context.getSlapStateTitle()
  else:
    result = d['text']
    if result.startswith('#access '):
      result = result[len('#access '):]

else:
  if state in ["start_requested", "stop_requested"]:
    result = 'Looking for a free partition'
  elif state in ["destroy_requested"]:
    result = 'Destroyed'

return result
