# This script might not be efficient to a large quantities of
# Compute Nodes
from DateTime import DateTime

kw.update({
  "follow_up_uid": context.getUid(),
  "portal_type": ['Instance Node', 'Remote Node', 'Compute Node', 'Instance Tree', 'Computer Network']
})

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

return [ i.getObject()
           for i in context.getPortalObject().portal_catalog(**kw)
             if filter_per_portal_type(i.getObject())]
