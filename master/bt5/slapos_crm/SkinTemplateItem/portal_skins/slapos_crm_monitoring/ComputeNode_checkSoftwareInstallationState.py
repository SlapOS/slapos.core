from DateTime import DateTime
portal = context.getPortalObject()

person = context.getSourceAdministrationValue(portal_type="Person")
if not person or \
   context.getMonitorScope("disabled") == "disabled" or \
   portal.ERP5Site_isSupportRequestCreationClosed():
  return 

software_installation_list = portal.portal_catalog(
      portal_type='Software Installation',
      default_aggregate_uid=context.getUid(),
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

  reference = software_installation.getReference()
  d = software_installation.getAccessStatus()
  if d.get("no_data", None) == 1:
    ticket_title = "[MONITORING] No information for %s on %s" % (reference, compute_node_reference)
    description = "The software release %s did not started to build on %s since %s" % \
        (software_installation.getUrlString(), compute_node_title, software_installation.getCreationDate())
  else:
    last_contact = DateTime(d.get('created_at'))
    if d.get("text").startswith("building"):
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
    support_request = person.Base_getSupportRequestInProgress(
      title=ticket_title,
      aggregate=software_installation.getRelativeUrl())

    if support_request is None:
      person.notify(support_request_title=ticket_title,
              support_request_description=description,
              aggregate=software_installation.getRelativeUrl())

      support_request_relative_url = context.REQUEST.get("support_request_relative_url")
      if support_request_relative_url is None:
        return

      support_request = portal.restrictedTraverse(support_request_relative_url)
    
    if support_request is None:
      return

    # Send Notification message
    notification_reference = 'slapos-crm-compute_node_software_installation_state.notification'
    notification_message = portal.portal_notifications.getDocumentValue(
                 reference=notification_reference)

    if notification_message is None:
      message = """%s""" % description
    else:
      mapping_dict = {'compute_node_title':context.getTitle(),
                      'compute_node_id':reference,
                      'last_contact':last_contact}

      message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict':mapping_dict})

    event = support_request.SupportRequest_getLastEvent(ticket_title)
    if event is None:
      support_request.notify(message_title=ticket_title, message=message)

    support_request_list.append(support_request)

return support_request_list
