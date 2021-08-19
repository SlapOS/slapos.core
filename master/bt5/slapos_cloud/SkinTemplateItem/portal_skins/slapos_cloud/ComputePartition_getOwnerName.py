instance = context.getAggregateRelatedValue(portal_type=["Software Instance"])
if instance is None:
  return None

owner = instance.getSpecialiseValue().getDestinationSectionValue()

return owner.getTitle()
