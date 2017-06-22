computer = state_change['object']
context.REQUEST.set('computer_certificate', None)
context.REQUEST.set('computer_certificate_url', None)
certificate_id_list = [x for x in
  computer.contentValues(portal_type="Certificate Access ID")
  if x.getValidationState() == 'validated']

if not len(certificate_id_list):
  raise ValueError('No certificate')

# XXX - considering that there is always one objects
certificate_id = certificate_id_list[0]
context.getPortalObject().portal_web_services.caucase_adapter\
  .revokeCertificate(certificate_id.getReference())

# Invalidate certificate
certificate_id.invalidate()
