from zExceptions import Unauthorized
edit_kw = {}

person = context.getPortalObject().portal_membership.getAuthenticatedMember().getUserValue()
if person != context.getParentValue():
  raise Unauthorized


if reference is not None:
  edit_kw["reference"] = reference

if password is not None:
  edit_kw["password"] = password

if len(edit_kw):
  context.edit(**edit_kw)
