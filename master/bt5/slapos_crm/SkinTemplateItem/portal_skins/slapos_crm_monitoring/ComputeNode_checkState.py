from DateTime import DateTime
portal = context.getPortalObject()

person = context.getSourceAdministrationValue(portal_type="Person")
if not person or \
   context.getMonitorScope("disabled") == "disabled" or \
   portal.ERP5Site_isSupportRequestCreationClosed():
  return

reference = context.getReference()
compute_node_title = context.getTitle()

node_ticket_title = "[MONITORING] Lost contact with compute_node %s" % reference
instance_ticket_title = "[MONITORING] Compute Node %s has a stalled instance process" % reference
ticket_title = node_ticket_title

description = ""
last_contact = "No Contact Information"
issue_document_reference = ""
notification_message_reference = 'slapos-crm-compute_node_check_state.notification'
now = DateTime()

d = context.getAccessStatus()
# Ignore if data isn't present.
should_notify = False
if d.get("no_data") == 1:
  should_notify = True
  description = "The Compute Node %s (%s)  has not contacted the server (No Contact Information)" % (
                  compute_node_title, reference)
else:
  last_contact = DateTime(d.get('created_at'))
  if (now - last_contact) > 0.01:
    should_notify = True
    description = "The Compute Node %s (%s) has not contacted the server for more than 30 minutes" \
    "(last contact date: %s)" % (compute_node_title, reference, last_contact)
  else:
    data_array  = context.ComputeNode_hasModifiedFile()
    if data_array:
      should_notify = True
      notification_message_reference = "slapos-crm-compute_node_check_modified_file.notification"
      ticket_title = "[MONITORING] Compute Node %s has modified file" % reference
      issue_document_reference = data_array.getReference()
      description = "The Compute Node %s (%s) has modified file: %s" % (compute_node_title, reference, issue_document_reference)

if not should_notify:
  # Since server is contacting, check for stalled processes
  ticket_title = instance_ticket_title
  notification_message_reference = 'slapos-crm-compute_node_check_stalled_instance_state.notification'
  last_contact = "No Contact Information"

  # If server has no partitions skip
  compute_partition_uid_list = [
    x.getUid() for x in context.contentValues(portal_type="Compute Partition")
    if x.getSlapState() == 'busy']

  if compute_partition_uid_list:
    instance_list = portal.portal_catalog(
      portal_type='Software Instance',
      default_aggregate_uid=compute_partition_uid_list)

    if instance_list:
      should_notify = True

    for instance in instance_list:
      instance_access_status = instance.getAccessStatus()
      if instance_access_status.get('no_data', None):
        # Ignore if there isnt any data
        continue

      # At lest one partition contacted in the last 24h30min.
      last_contact = max(DateTime(instance_access_status.get('created_at')), last_contact)
      if (now - DateTime(instance_access_status.get('created_at'))) < 1.05:
        should_notify = False
        break

    if should_notify:
      description = "The Compute Node %s (%s) didnt process its instances for more than 24 hours, last contact: %s" % (
        context.getTitle(), context.getReference(), last_contact)

if should_notify:
  support_request = person.Base_getSupportRequestInProgress(
      title=node_ticket_title,
      aggregate=context.getRelativeUrl())

  if support_request is None:
    support_request = person.Base_getSupportRequestInProgress(
      title=ticket_title,
      aggregate=context.getRelativeUrl())

  if support_request is None:
    person.notify(support_request_title=ticket_title,
      support_request_description=description,
      aggregate=context.getRelativeUrl())

    support_request_relative_url = context.REQUEST.get("support_request_relative_url")
    if support_request_relative_url is None:
      return

    support_request = portal.restrictedTraverse(support_request_relative_url)

  if support_request is None:
    return

  # Send Notification message
  notification_message = portal.portal_notifications.getDocumentValue(
    reference=notification_message_reference)

  if notification_message is None:
    message = """%s""" % description
  else:
    mapping_dict = {'compute_node_title':context.getTitle(),
                    'compute_node_id':reference,
                    'last_contact':last_contact,
                    'issue_document_reference': issue_document_reference}
    message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict': mapping_dict})

  event = support_request.SupportRequest_getLastEvent(ticket_title)
  if event is None:
    support_request.notify(message_title=ticket_title, message=message)

  return support_request
