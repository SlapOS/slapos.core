if context.getAggregate() is None:
  return context.Base_translateString("Not allocated")

partition = context.getAggregateValue(checked_permission="View")
if partition is not None:
  return "%s (%s)" % (
    partition.getParentValue().getReference(), 
    partition.getReference())


return context.Base_translateString("Restricted information")
