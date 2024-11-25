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

if context.getPortalType() == 'Slave Instance' and compute_node.getPortalType() == "Compute Node":
  software_instance = compute_partition.getAggregateRelated(portal_type='Software Instance')
  if software_instance is None:
    # Slave instance is allocated but the software instance was already destroyed
    error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-slave-on-destroyed-instance.notification'
    error_dict = updateErrorDictWithError(error_dict)
    error_dict['message'] = "%s is allocated on a destroyed software instance (already removed)." % context.getTitle()
    error_dict['ticket_description'] = error_dict['message']
    return error_dict


sla_dict = context.getSlaXmlAsDict()
instance_sla_error_list = []
instance_project_reference = context.getFollowUpReference()
project_reference = compute_node.getFollowUpReference()

if project_reference != instance_project_reference:
  instance_sla_error_list.append("Instance and Compute node project do not match on: %s (%s != %s)" % (
    context.getTitle(), project_reference, instance_project_reference))

if sla_dict:
  instance_title = context.getTitle()
  # Simple check of instance SLAs
  if "computer_guid" in sla_dict:
    computer_guid = sla_dict.pop("computer_guid")
    if compute_node.getReference() != computer_guid:
      instance_sla_error_list.append('computer_guid do not match on: %s (%s != %s)' % (
        instance_title, computer_guid, compute_node.getReference()))

  if "instance_guid" in sla_dict:
    instance_guid = sla_dict.pop("instance_guid")
    if context.getPortalType() != 'Slave Instance':
      instance_sla_error_list.append('instance_guid is provided to a Software Instance: %s' % instance_title)
    else:
      if compute_node.getPortalType() == "Remote Node":
        instance_sla_error_list.append('instance_guid provided on %s and it is allocated on a REMOTE NODE' % instance_title)
      else:
        software_instance = compute_partition.getAggregateRelatedValue(portal_type='Software Instance')
        if software_instance is not None and software_instance.getReference() != instance_guid:
          instance_sla_error_list.append('instance_guid do not match on: %s (%s != %s)' % (
              instance_title, instance_guid, software_instance.getReference()))

  if 'network_guid' in sla_dict:
    network_guid = sla_dict.pop('network_guid')
    network_reference = compute_node.getSubordinationReference()
    if network_reference != network_guid:
      instance_sla_error_list.append('network_guid do not match on: %s (%s != %s)' % (
        instance_title, network_guid, network_reference))

  if 'project_guid' in sla_dict:
    project_guid = sla_dict.pop("project_guid")
    if project_reference != project_guid:
      instance_sla_error_list.append('project_guid do not match on: %s (%s != %s)' % (
        instance_title, project_guid, project_reference))

if instance_sla_error_list:
  # Slave instance is allocated but the software instance was already destroyed
  error_dict['notification_message_reference'] = 'slapos-crm-instance-tree-has-invalid-sla.notification'
  error_dict = updateErrorDictWithError(error_dict)
  error_text = ""
  for _e in instance_sla_error_list:
    error_text += "  * %s\n" % _e

  error_dict['error_text'] = error_text
  error_dict['ticket_description'] = """%s has invalid Service Level Aggrement.

Detected inconsistencies:

%s""" % (instance_title, error_text)
  error_dict['message'] = error_dict['ticket_description']
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
