for si in context.getAggregateRelatedValueList(portal_type=["Software Instance"]):
  obj = si.getObject()  

  if obj.getValidationState() != "validated":
    continue
  if obj.getSlapState() == "destroy_requested":
    continue

  return obj.getLastAccessDate()
  
return ""
