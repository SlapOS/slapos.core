"""Check login is available locally and globally for instance with SSO.
Parameters:
value -- field value (string)
REQUEST -- standard REQUEST variable"""
portal = context.getPortalObject()

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

#check no pending credential request with this email
#Don't take in case the current credential
previous_credential_request = portal.portal_catalog.getResultValue(
  portal_type='Credential Request',
  default_email_text=value,
  uid="NOT %s" % context.getUid(),
  validation_state=["draft", "submitted"]
)
if previous_credential_request is not None:
  return False

#check no pending credential request with this email
#Don't take in case the current credential
previous_person = portal.portal_catalog.getResultValue(
  portal_type='Person',
  default_email_text=value
)
if previous_person is not None:
  return False

return True
