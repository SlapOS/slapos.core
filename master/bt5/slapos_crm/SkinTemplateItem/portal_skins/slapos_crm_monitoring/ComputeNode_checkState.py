from DateTime import DateTime
portal = context.getPortalObject()

if (context.getMonitorScope() == "disabled") or \
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
      aggregate__uid=compute_partition_uid_list)

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

  project = context.getFollowUpValue()
  support_request = project.Project_createSupportRequestWithCausality(
    ticket_title,
    description,
    causality=context.getRelativeUrl(),
    destination_decision=project.getDestination()
  )

  if support_request is None:
    return

  support_request.Ticket_createProjectEvent(
    ticket_title, 'outgoing', 'Web Message',
    portal.service_module.slapos_crm_information.getRelativeUrl(),
    text_content=description,
    content_type='text/plain',
    notification_message=notification_message_reference,
    #language=XXX,
    substitution_method_parameter_dict={
      'compute_node_title':context.getTitle(),
      'compute_node_id':reference,
      'last_contact':last_contact,
      'issue_document_reference': issue_document_reference
    }
  )

  return support_request
