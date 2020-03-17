from zExceptions import Unauthorized
from DateTime import DateTime

portal = context.getPortalObject()
if portal.portal_membership.isAnonymousUser():
  raise Unauthorized("You cannot invoke this API as Annonymous")

if not context.SoftwareInstance_isUserAllowedToDestroy():
  raise Unauthorized("You cannot destroy this %s." % context.getPortalType())

if context.getSlapState() not in ["start_requested", "stop_requested"]:
  return context.Base_redirect(keep_items={"portal_status_message": "This %s is on %s state and cannot be destroyed." \
    % (context.getPortalType(), context.getSlapState())})

# It is used a external method as portal_slap._storeLastData cannot be invoked
# from a python script
context.SoftwareInstance_renameAndRequestDestroy()

# Request Destroy on all Slaves allocated on the same partition
computer_partition = context.getAggregateValue(
  portal_type="Computer Partition")

if computer_partition is not None:
  for slave in computer_partition.getAggregateRelatedValueList(
    portal_type="Slave Instance"):
    slave.SoftwareInstance_renameAndRequestDestroy()

return context.Base_redirect(keep_items={"portal_status_message": "Destroy requested."})
