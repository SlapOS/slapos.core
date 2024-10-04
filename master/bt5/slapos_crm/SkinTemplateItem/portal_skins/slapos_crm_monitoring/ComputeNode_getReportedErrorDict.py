portal = context.getPortalObject()
compute_node = context

reference = context.getReference()
compute_node_title = context.getTitle()
d = compute_node.getAccessStatus()

error_dict = {
        'should_notify': None,
        'ticket_title': None,
        'ticket_description': None,
        'notification_message_reference': None,
        'compute_node_title': compute_node_title,
        'compute_node_id': reference,
        'last_contact': None,
        'issue_document_reference': None
      }


if compute_node.getMonitorScope() == "disabled":
  if batch_mode:
    return None
  for i in ['ticket_title', 'ticket_description', 'last_contact']:
    error_dict[i] = "Monitor is disabled on this Compute Node."
  return error_dict

if d.get("no_data") == 1:
  error_dict['last_contact'] = "No Contact Information"
  if batch_mode:
    return error_dict['last_contact']

  error_dict['ticket_title'] = "Lost contact with compute_node %s" % reference
  error_dict['ticket_description'] = \
    "The Compute Node %s (%s)  has not contacted the server (No Contact Information)" % (
                  compute_node_title.getTitle(), reference())
  error_dict['notification_message_reference'] = 'slapos-crm-compute_node_check_state.notification'
  error_dict['should_notify'] = True
  return error_dict

last_contact = DateTime(d.get('created_at'))
now = DateTime()
if (now - last_contact) > 0.01:
  error_dict['should_notify'] = True
  error_dict['ticket_title'] = "Lost contact with compute_node %s" % reference
  error_dict['last_contact'] = last_contact
  if batch_mode:
    return error_dict['last_contact']
  error_dict['notification_message_reference'] = 'slapos-crm-compute_node_check_state.notification'
  error_dict['ticket_description'] = "The Compute Node %s (%s) has not contacted the server for more than 30 minutes" \
    "(last contact date: %s)" % (compute_node_title, reference, last_contact)
  return error_dict

data_array  = context.ComputeNode_hasModifiedFile()
if data_array:
  error_dict['last_contact'] = last_contact
  if batch_mode:
    return error_dict['last_contact']
  error_dict['should_notify'] = True
  error_dict['notification_message_reference'] = "slapos-crm-compute_node_check_modified_file.notification"
  error_dict['ticket_title'] = "Compute Node %s has modified file" % reference
  error_dict['issue_document_reference'] = data_array.getReference()
  error_dict['ticket_description'] = "The Compute Node %s (%s) has modified file: %s" % (
    compute_node_title, reference, error_dict['issue_document_reference'])
  return error_dict

# Since server is contacting, check for stalled processes
# If server has no partitions skip
compute_partition_uid_list = [
    x.getUid() for x in context.contentValues(portal_type="Compute Partition")
    if x.getSlapState() == 'busy']

if compute_partition_uid_list:
  instance_list = portal.portal_catalog(
    portal_type='Software Instance',
    aggregate__uid=compute_partition_uid_list)
  
  should_notify = True
  instance_last_contact = -1
  for instance in instance_list:
    instance_access_status = instance.getAccessStatus()
    if instance_access_status.get('no_data', None):
      # Ignore if there isnt any data
      continue

    # At lest one partition contacted in the last 24h30min.
    instance_last_contact = max(DateTime(instance_access_status.get('created_at')),
                                instance_last_contact)
    if (now - DateTime(instance_access_status.get('created_at'))) < 1.05:
      should_notify = False
      break
   
  if len(instance_list) and should_notify:
    if instance_last_contact == -1:
      error_dict['last_contact'] = "No Contact Information"
    else:
      error_dict['last_contact'] = instance_last_contact

    if batch_mode:
      return error_dict['last_contact']

    error_dict['should_notify'] = True
    error_dict['notification_message_reference'] = "slapos-crm-compute_node_check_modified_file.notification"
    error_dict['ticket_title'] = "Compute Node %s has a stalled instance process" % reference
    error_dict['ticket_description'] = "The Compute Node %s (%s) didnt process its instances for more than 24 hours, last contact from the node: %s" % (
      compute_node_title, reference, last_contact)
    return error_dict

if batch_mode:
  return
return error_dict
