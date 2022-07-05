from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

return portal.portal_catalog.countResults(
    portal_type=["ERP5 Login", "Google Login", "Facebook Login"],
    reference=reference,
    validation_state="validated"
)[0][0] > 0
