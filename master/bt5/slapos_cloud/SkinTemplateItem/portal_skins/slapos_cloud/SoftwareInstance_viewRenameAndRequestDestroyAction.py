from zExceptions import Unauthorized
from DateTime import DateTime

portal = context.getPortalObject()
if portal.portal_membership.isAnonymousUser():
  raise Unauthorized("You cannot invoke this API as Annonymous")

if context.getSlapState() not in ["stop_requested", "start_requested"]:
  return context.Base_redirect(keep_items={"portal_status_message": "This %s is on %s state and cannot be destroyed." \
    % (context.getPortalType(), context.getSlapState())})

# It is used a external method as portal_slap._storeLastData cannot be invoked
# from a python script
context.SoftwareInstance_renameAndRequestDestroy()

return context.Base_redirect(keep_items={"portal_status_message": "Destroy requested."})
