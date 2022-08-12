from Products.ERP5Type.Message import translateString

sale_supply = context

sale_supply.validate()

return sale_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('Sale Supply validated.')}
)
