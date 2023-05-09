partition = context.getAggregateValue()
if partition is not None:
  return "%s (%s)" % (
    partition.getParentValue().getReference(), 
    partition.getReference())

if context.getAggregate() is None:
  return context.Base_translateString("Not allocated")
  
return context.Base_translateString("Not allowed")
