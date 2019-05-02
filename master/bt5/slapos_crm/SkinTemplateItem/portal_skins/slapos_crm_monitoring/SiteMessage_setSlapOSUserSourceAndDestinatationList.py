from DateTime import DateTime

portal = context.getPortalObject()

open_sale_order_list = portal.portal_catalog(
  portal_type="Open Sale Order",
  children_portal_type="Open Sale Order Line",
  validation_state="validated")

context.edit(
  source=context.organisation_module.slapos,
  destination=[i.getDestination() for i in open_sale_order_list])

return context.Base_redirect()
