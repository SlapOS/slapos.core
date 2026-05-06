from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

open_sale_order = context
while open_sale_order.getPortalType() != 'Open Sale Order':
  open_sale_order = open_sale_order.getParentValue()

return open_sale_order.OpenSaleOrder_archiveIfUnusedItem()
