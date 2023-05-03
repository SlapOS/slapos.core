partition = context.getAggregateValue()
if partition is not None:
  return "%s (%s)" % (
    partition.getParentValue().getReference(), 
    partition.getReference())

return ""
