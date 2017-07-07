computer = state_change['object']
context.REQUEST.set('computer_certificate', None)
context.REQUEST.set('computer_certificate_url', None)
certificate_login_list = [x for x in
  computer.contentValues(portal_type="Certificate Login")
  if x.getValidationState() == 'validated']

if not len(certificate_login_list):
  raise ValueError('No certificate')

# XXX - considering that there is always one objects
certificate_login = certificate_login_list[0]
context.getPortalObject().portal_web_services.caucase_adapter\
  .revokeCertificate(certificate_login.getReference())

# Invalidate certificate
certificate_login.invalidate()
