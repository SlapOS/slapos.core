portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  method_id='OpenSaleOrder_reindexIfIndexedBeforeLine',
  portal_type="Open Sale Order",
  children_portal_type="Open Sale Order Line",
  uid=[i.uid for i in portal.ERP5Site_zGetOpenOrderWithModifiedLineUid()],
  activate_kw={'tag': tag},
)

context.activate(after_tag=tag).getId()
