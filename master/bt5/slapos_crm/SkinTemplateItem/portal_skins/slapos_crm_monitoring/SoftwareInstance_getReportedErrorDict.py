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
        'error_text': None,
        'message': None
      }

# Nothing to do
if context.getSlapState() != "start_requested":
  return error_dict

def updateErrorDictWithError(_error_dict):
  _error_dict['should_notify'] = True
  _error_dict['ticket_title'] = "Instance Tree %s is failing." % _error_dict['instance_tree_title']
  return _error_dict

compute_partition = context.getAggregateValue(portal_type="Compute Partition")
if compute_partition is None:
  error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-instance-allocation.notification'
  error_dict['message'] = "%s is not allocated." % context.getTitle()
  error_dict['ticket_description'] = error_dict['message']
  return updateErrorDictWithError(error_dict)

compute_node = compute_partition.getParentValue()
if compute_node.getPortalType() == "Compute Node" and \
     compute_node.getAllocationScope() == 'close/forever':
  # Closed compute_nodes like this might contains unremoved instances hanging there
  error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-instance-on-close-computer.notification'
  error_dict = updateErrorDictWithError(error_dict)
  error_dict['message'] = "%s is allocated on a Compute node that is closed forever." % context.getTitle()
  error_dict['ticket_description'] = error_dict['message']
  return error_dict

# Skip to check if monitor disabled on the compute node.
# Remote node has no state.
if (compute_node.getPortalType() == "Compute Node") and (compute_node.getMonitorScope() != "enabled"):
  error_dict['ticket_title'] = "Monitor is disabled on the Compute Node"
  error_dict['ticket_description'] = error_dict['ticket_title']
  return error_dict

d = context.getAccessStatus()
# Ignore if data isn't present.
if d.get("no_data", None) == 1:
  error_dict['ticket_title'] = "Not possible to connect"
  error_dict['ticket_description'] = "Not possible to connect"
  return error_dict

error_dict['error_text'] = d['text']
error_dict['last_contact'] = DateTime(d.get('created_at'))
error_dict['since'] = DateTime(d.get('since'))
if error_dict['error_text'].startswith('#error '):
  if ((DateTime()-error_dict['since'])*24*60) > tolerance:
    error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-instance-state.notification'
    description = "%s is reporting errors. \n\nMessage: %s" % (context.getTitle(), str(error_dict['error_text']))
    error_dict['ticket_description'] = description
    # Longer form for consistency.
    error_dict['message'] = "%s has error (%s, %s at %s)" % (
      context.getReference(), context.getTitle(), context.getUrlString(), compute_node.getReference())
    return updateErrorDictWithError(error_dict)

return error_dict
