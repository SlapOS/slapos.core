from DateTime import DateTime

tolerance = DateTime() - 0.5
software_installation = context
reference = software_installation.getReference()
compute_node_title = software_installation.getAggregateTitle()
d = software_installation.getAccessStatus()

error_dict = {
        'should_notify': None,
        'ticket_title': None,
        'ticket_description': None,
        'notification_message_reference': 'slapos-crm-compute_node_software_installation_state.notification',
        'compute_node_title': compute_node_title,
        'compute_node_id': reference,
        'last_contact': None,
      }

if (software_installation.getCreationDate() > tolerance) or \
    (software_installation.getSlapState() != 'start_requested') or \
    (d.get("no_data", None) == 1) or \
    (d.get("text").startswith("#access")):
  if batch_mode:
    return None
  return error_dict

last_contact = DateTime(d.get('created_at'))
if d.get("text").startswith("#building"):
  error_dict['last_contact'] = last_contact
  if batch_mode:
    return error_dict['last_contact']

  error_dict['should_notify'] = True
  error_dict['ticket_title'] = "%s is building for too long on %s" % (
      reference, software_installation.getAggregateReference())
  error_dict['ticket_description'] = "The software release %s is building for mode them 12 hours on %s, started on %s" % \
          (software_installation.getUrlString(),
           software_installation.getAggregateTitle(),
           software_installation.getCreationDate())
  return error_dict

if d.get("text").startswith("#error"):
  error_dict['last_contact'] = last_contact
  if batch_mode:
    return error_dict['last_contact']

  error_dict['should_notify'] = True
  error_dict['ticket_title'] = "%s is failing to build on %s" % (reference, software_installation.getAggregateReference())
  error_dict['ticket_description'] = "The software release %s is failing to build for too long on %s, started on %s" % \
    (software_installation.getUrlString(),
     software_installation.getAggregateTitle(),
     software_installation.getCreationDate())
  return error_dict

if batch_mode:
  return None
return error_dict
