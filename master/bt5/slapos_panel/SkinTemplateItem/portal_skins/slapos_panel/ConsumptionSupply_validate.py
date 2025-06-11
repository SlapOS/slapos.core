from Products.ERP5Type.Message import translateString

consumption_supply = context

consumption_supply.validate()

return consumption_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('Consumption Supply validated.')}
)
