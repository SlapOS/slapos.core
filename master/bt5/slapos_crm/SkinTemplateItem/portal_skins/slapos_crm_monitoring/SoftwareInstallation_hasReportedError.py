from DateTime import DateTime

if tolerance is None:
  tolerance = DateTime() - 0.5

software_installation = context
reference = software_installation.getReference()
d = software_installation.getAccessStatus()
def return_ok(batch_mode):
  if batch_mode:
    return None
  return None, None, None, None

if software_installation.getCreationDate() > tolerance:
  return return_ok(batch_mode)

if software_installation.getSlapState() != 'start_requested':
  return return_ok(batch_mode)

if d.get("no_data", None) == 1:
  return return_ok(batch_mode)

if d.get("text").startswith("#access"):
  return return_ok(batch_mode)

last_contact = DateTime(d.get('created_at'))
if d.get("text").startswith("#building"):
  if batch_mode:
    # is it a problem...?
    return last_contact

  should_notify = True
  ticket_title = "[MONITORING] %s is building for too long on %s" % (reference, software_installation.getAggregateReference())
  description = "The software release %s is building for mode them 12 hours on %s, started on %s" % \
          (software_installation.getUrlString(), software_installation.getAggregateTitle(), software_installation.getCreationDate())
  return should_notify, ticket_title, description, last_contact

if d.get("text").startswith("#error"):
  if batch_mode:
    return DateTime(d.get('created_at'))

  should_notify = True
  ticket_title = "[MONITORING] %s is failing to build on %s" % (reference, software_installation.getAggregateReference())
  description = "The software release %s is failing to build for too long on %s, started on %s" % \
    (software_installation.getUrlString(), software_installation.getAggregateTitle(), software_installation.getCreationDate())
  return should_notify, ticket_title, description, last_contact
