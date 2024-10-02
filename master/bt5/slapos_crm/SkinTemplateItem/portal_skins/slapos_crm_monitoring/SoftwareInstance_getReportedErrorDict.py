from DateTime import DateTime
error_dict = {
        'should_notify': None,
        'ticket_title': None,
        'ticket_description': None,
        'instance_tree_title':context.getSpecialiseTitle(),
        'instance': context.getTitle(),
        'notification_message_reference': None,
        'last_contact': None,
        'since': None,
        'message': None
      }

# Nothing to do
if context.getSlapState() != "start_requested":
  if batch_mode:
    return
  return error_dict

def updateErrorDictWithError(_error_dict):
  _error_dict['should_notify'] = True
  _error_dict['ticket_title'] = "Instance Tree %s is failing." % context.getTitle()
  description = "%s contains software instances which are unallocated or reporting errors." % (
      context.getTitle())
  if _error_dict['message']:
    description += "\n\nMessage: %s" % str(_error_dict['message'])
  _error_dict['ticket_description'] = description
  return _error_dict

compute_partition = context.getAggregateValue(portal_type="Compute Partition")
if compute_partition is None:
  error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-instance-allocation.notification'
  return updateErrorDictWithError(error_dict)

if context.getPortalType() == 'Slave Instance':
  # We skip if the the slave is already allocated.
  if batch_mode:
    return
  return error_dict

# Skip to check if monitor disabled on the compute node.
# Remote node has no state.
if compute_partition.getParentValue().getPortalType() != "Compute Node":
  if batch_mode:
    return
  portal_type = compute_partition.getParentValue().getPortalType()
  error_dict['ticket_title'] = "Instance is allocated on a %s" % portal_type
  error_dict['ticket_description'] = error_dict['ticket_title']
  return error_dict

if compute_partition.getParentValue().getMonitorScope() != "enabled":
  if batch_mode:
    return
  error_dict['ticket_title'] = "Monitor is disabled on the Compute Node"
  error_dict['ticket_description'] = error_dict['ticket_title']
  return error_dict

d = context.getAccessStatus()
# Ignore if data isn't present.
if d.get("no_data", None) == 1:
  if batch_mode:
    return
  error_dict['ticket_title'] = "Not possible to connect"
  error_dict['ticket_description'] = "Not possible to connect"
  return error_dict

error_dict['message'] = d['text']
error_dict['last_contact'] = DateTime(d.get('created_at'))
error_dict['since'] = DateTime(d.get('since'))
if error_dict['message'].startswith('#error '):
  if ((DateTime()-error_dict['since'])*24*60) > tolerance:
    error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-instance-state.notification'
    if batch_mode:
      return True
    return updateErrorDictWithError(error_dict)

if batch_mode:
  return None
return error_dict
