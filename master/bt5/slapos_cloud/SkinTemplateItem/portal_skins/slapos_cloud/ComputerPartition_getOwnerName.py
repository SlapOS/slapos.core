instance = context.getAggregateRelatedValue(portal_type=["Software Instance", "Slave Instance"])
if instance is None:
  return None

owner = instance.getSpecialiseValue().getDestinationSectionValue()

return owner.getTitle()
