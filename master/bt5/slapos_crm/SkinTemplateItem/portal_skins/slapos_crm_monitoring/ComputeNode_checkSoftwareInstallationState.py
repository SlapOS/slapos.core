from DateTime import DateTime
portal = context.getPortalObject()

if context.getMonitorScope() == "disabled":
  return
  
project = context.getFollowUpValue()
if project.Project_isSupportRequestCreationClosed():
  return

software_installation_list = portal.portal_catalog(
      portal_type='Software Installation',
      aggregate__uid=context.getUid(),
      validation_state='validated',
      sort_on=(('creation_date', 'DESC'),)
    )

support_request_list = []
should_notify = True

tolerance = DateTime() - 0.5
for software_installation in software_installation_list:
  should_notify = False
  should_notify, ticket_title, description, last_contact = \
    software_installation.SoftwareInstallation_hasReportedError(
      tolerance=tolerance)

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

    notification_message_reference = 'slapos-crm-compute_node_software_installation_state.notification'
    support_request.Ticket_createProjectEvent(
      ticket_title, 'outgoing', 'Web Message',
      portal.service_module.slapos_crm_information.getRelativeUrl(),
      text_content=description,
      content_type='text/plain',
      notification_message=notification_message_reference,
      #language=XXX,
      substitution_method_parameter_dict={
        'compute_node_title':context.getTitle(),
        # Maybe a mistake on compute_node_id
        'compute_node_id': software_installation.getReference(),
        'last_contact': last_contact
      }
    )

    support_request_list.append(support_request)

return support_request_list
