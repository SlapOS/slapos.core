# Note: can be cached for 24h if needed: the list is not expected to change often, nor to ever reach even 10 entries.
portal = context.getPortalObject()
return portal.account_module.searchFolder(
  strict_account_type_uid=portal.portal_categories.account_type.liability.payable.getUid(),
  validation_state='validated',
)
