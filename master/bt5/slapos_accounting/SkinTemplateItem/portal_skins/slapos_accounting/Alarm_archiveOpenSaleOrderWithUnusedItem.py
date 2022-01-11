portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Open Sale Order',
  validation_state='validated',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  method_id='OpenSaleOrder_archiveIfUnusedItem',
  activate_kw={'tag': tag}
)
context.activate(after_tag=tag).getId()
