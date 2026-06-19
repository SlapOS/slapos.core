allocation_supply = context.getParentValue()

assert allocation_supply.getPortalType() == 'Allocation Supply'
assert allocation_supply.getValidationState() == 'deleted'

# Delete all Allocation Supply Lines, as parent is 'deleted'.
# This allows to delete some Software Product, which were never used/instanciated

allocation_supply.manage_delObjects([i for i in allocation_supply.objectIds()])
allocation_supply.reindexObject(activate_kw=activate_kw)
