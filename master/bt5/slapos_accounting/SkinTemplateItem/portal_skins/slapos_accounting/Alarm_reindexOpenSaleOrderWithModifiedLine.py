portal = context.getPortalObject()

for line in portal.ERP5Site_zGetOpenOrderWithModifiedLineUid():
  context.activate(activity="SQLQueue",tag=tag).OpenSaleOrder_reindexIfIndexedBeforeLine(uid=line.uid)

context.activate(after_tag=tag).getId()
