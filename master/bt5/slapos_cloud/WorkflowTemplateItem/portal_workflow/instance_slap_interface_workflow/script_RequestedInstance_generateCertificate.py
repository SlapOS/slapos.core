instance = state_change['object']

if instance.getDestinationReference() is not None:
  raise ValueError("Certificate still active.")

if instance.getPortalType() != "Software Instance":
  # Skip if the instance isn't a Software Instance, 
  # since Shared Instances cannot find the object.
  return

ca = context.getPortalObject().portal_certificate_authority
certificate_dict = ca.getNewCertificate(instance.getReference())

edit_kw = {'destination_reference' : certificate_dict['id'],
           'ssl_key' : certificate_dict['key'],
           'ssl_certificate': certificate_dict['certificate']
          }

instance.edit(**edit_kw)
