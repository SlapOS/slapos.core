from zExceptions import Unauthorized
import json

portal = context.getPortalObject()

person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if (person is None) or (person.getUid() != context.getUid()):
  raise Unauthorized("You are not allowed to create login to a different user")

if context.Person_testLoginExistence(reference=reference):
  context.REQUEST.RESPONSE.setStatus('406')
  return json.dumps(
    portal.Base_translateString("Login already exists"))

try:
  erp5_login = context.newContent(
    portal_type = "ERP5 Login",
    reference=reference,
    password=password
  )
  erp5_login.validate()
except ValueError as e:
  context.REQUEST.RESPONSE.setStatus('406')
  return json.dumps(str(portal.Base_translateString(e)))

return json.dumps(erp5_login.getRelativeUrl())
