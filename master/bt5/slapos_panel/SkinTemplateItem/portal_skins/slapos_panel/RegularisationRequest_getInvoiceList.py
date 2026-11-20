entity = context.getDestinationValue()
if not entity:
  return []

return entity.Entity_getOutstandingInvoiceList()
