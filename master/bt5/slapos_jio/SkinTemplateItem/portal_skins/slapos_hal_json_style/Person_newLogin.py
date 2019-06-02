from zExceptions import Unauthorized

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person.getUid() != context.getUid():
  raise Unauthorized("You are not allowed to create login to a different user")

if context.Person_testLoginExistence(reference=reference):
  raise Unauthorized("Login already exists")

erp5_login = context.newContent(
    portal_type = "ERP5 Login",
    reference=reference,
    password=password
)
erp5_login.validate()

return erp5_login.getRelativeUrl()
