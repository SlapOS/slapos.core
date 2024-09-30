from DateTime import DateTime
portal = context.getPortalObject()

if (context.getMonitorScope() == "disabled"):
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
compute_node_reference = context.getReference()
compute_node_title = context.getTitle()
should_notify = True

tolerance = DateTime()-0.5
for software_installation in software_installation_list:
  should_notify = False
  if software_installation.getCreationDate() > tolerance:
    # Give it 12 hours to deploy.
    continue

  if software_installation.getSlapState() != 'start_requested':
    continue

  reference = software_installation.getReference()
  d = software_installation.getAccessStatus()
  if d.get("no_data", None) == 1:
    #should_notify = True
    # We do not create if there is no information for the compilation
    # it should be reported by more global alarm related to the compute node itself
    last_contact = "No Contact Information"
    ticket_title = "[MONITORING] No information for %s on %s" % (reference, compute_node_reference)
    description = "The software release %s did not started to build on %s since %s" % \
        (software_installation.getUrlString(), compute_node_title, software_installation.getCreationDate())
  else:
    last_contact = DateTime(d.get('created_at'))
    if d.get("text").startswith("#building"):
      should_notify = True
      ticket_title = "[MONITORING] %s is building for too long on %s" % (reference, compute_node_reference)
      description = "The software release %s is building for mode them 12 hours on %s, started on %s" % \
              (software_installation.getUrlString(), compute_node_title, software_installation.getCreationDate())
    elif d.get("text").startswith("#access"):
      # Nothing to do.
      pass
    elif d.get("text").startswith("#error"):
      should_notify = True
      ticket_title = "[MONITORING] %s is failing to build on %s" % (reference, compute_node_reference)
      description = "The software release %s is failing to build for too long on %s, started on %s" % \
        (software_installation.getUrlString(), compute_node_title, software_installation.getCreationDate())

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
        'compute_node_id':reference,
        'last_contact':last_contact
      }
    )

    support_request_list.append(support_request)

return support_request_list
