portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
  validation_state='validated',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  aggregate__validation_state=['invalidated', 'archived'],
  method_id='OpenSaleOrderLine_archiveIfUnusedItem',
  # Increase priority to not block other activities
  # Put a really high value, as this alarm is not critical
  # And should not slow down others
  activate_kw={'tag': tag, 'priority': 5}
)
context.activate(after_tag=tag).getId()
