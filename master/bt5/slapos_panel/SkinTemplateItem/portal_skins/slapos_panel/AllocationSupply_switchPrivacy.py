from Products.ERP5Type.Message import translateString

allocation_supply = context

if context.hasDestination():
  # private
  allocation_supply.edit(destination=None)
  msg = 'Allocation Supply is now public.'
else:
  # public
  # Make it private for the project owner
  # Only copy the path, as current user may not have access to the entity
  allocation_supply.edit(destination=allocation_supply.getDestinationProjectValue().getDestination())
  msg = 'Allocation Supply is now private.'

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString(msg)}
)
