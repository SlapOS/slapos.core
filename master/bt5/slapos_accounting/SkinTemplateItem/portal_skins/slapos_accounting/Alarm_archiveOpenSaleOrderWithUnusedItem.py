portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Open Sale Order',
  validation_state='validated',
  ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  method_id='OpenSaleOrder_archiveIfUnusedItem',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  # Put a really high value, as this alarm is not critical
  # And should not slow down others
  activate_kw={'tag': tag, 'priority': 5}
)
context.activate(after_tag=tag).getId()
