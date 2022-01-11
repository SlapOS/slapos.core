from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

document = context

document.updateLocalRolesOnSecurityGroups()

if document.getPortalType() in ['Support Request', 'Upgrade Decision']:
  portal = context.getPortalObject()

  if activate_kw is None:
    activate_kw = {}

  portal.portal_catalog.searchAndActivate(
    portal_type=portal.getPortalEventTypeList(),
    follow_up__uid=document.getUid(),
    method_id="updateLocalRolesOnSecurityGroups",
    activate_kw=activate_kw
  )
