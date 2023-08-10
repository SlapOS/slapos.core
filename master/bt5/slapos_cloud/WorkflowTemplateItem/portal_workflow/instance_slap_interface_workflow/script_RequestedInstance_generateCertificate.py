instance = state_change['object']
if instance.getPortalType() != "Software Instance":
  # Skip if the instance isn't a Software Instance, 
  # since Shared Instances cannot find the object.
  return

for certificate_login in instance.objectValues(
  portal_type=["Certificate Login"]):
  if certificate_login.getValidationState() == "validated":
    raise ValueError('Certificate still active.')
    
# Include Certificate Login so Instance become a User
certificate_login = instance.newContent(
  portal_type="Certificate Login")
certificate_dict = certificate_login.getCertificate()
certificate_login.validate()

# Keep this here?
edit_kw = {'ssl_key' : certificate_dict['key'],
           'ssl_certificate': certificate_dict['certificate']}
instance.edit(**edit_kw)
