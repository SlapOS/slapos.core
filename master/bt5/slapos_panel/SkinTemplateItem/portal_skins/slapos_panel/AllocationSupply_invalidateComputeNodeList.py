from Products.ERP5Type.Message import translateString

allocation_supply = context

allocation_supply.invalidate()

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('Allocation Supply invalidated.')}
)
