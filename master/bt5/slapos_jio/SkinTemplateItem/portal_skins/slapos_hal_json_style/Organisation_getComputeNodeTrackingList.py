# This script might not be efficient to a large quantities of
# Compute Nodes
portal = context.getPortalObject()

def filter_per_portal_type(document):
  if document.getPortalType() == "Compute Node" \
      and document.getAllocationScope() != "close/forever":
    return document
  elif document.getPortalType() == "Instance Tree" \
      and document.getSlapState() != "destroy_requested":
    return document
  elif document.getPortalType() == "Computer Network" \
      and document.getValidationState() == "validated":
    return document

return portal.portal_catalog(uid=[i.uid
           for i in context.portal_simulation.getCurrentTrackingList(
             node_uid=context.getUid(), at_date=DateTime())
             if filter_per_portal_type(i.getObject())], **kw)
