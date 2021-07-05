# This script might not be efficient to a large quantities of
# Computers

from DateTime import DateTime

kw = {"node_uid": context.getUid(),
      "at_date": DateTime()}

def filter_per_portal_type(document):
  if document.getPortalType() == "Computer" \
      and document.getAllocationScope() != "close/forever":
    return document
  elif document.getPortalType() == "Instance Tree" \
      and document.getSlapState() != "destroy_requested":
    return document
  elif document.getPortalType() == "Computer Network" \
      and document.getValidationState() == "validated":
    return document

return [ i.getObject()
           for i in context.portal_simulation.getCurrentTrackingList(**kw)
             if filter_per_portal_type(i.getObject())]
