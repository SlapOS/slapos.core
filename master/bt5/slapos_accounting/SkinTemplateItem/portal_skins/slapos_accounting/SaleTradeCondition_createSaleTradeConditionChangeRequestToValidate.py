portal = context.getPortalObject()
change_request = portal.sale_trade_condition_change_request_module.newContent(
  portal_type='Sale Trade Condition Change Request',
  specialise_value=context,
  title=context.getTitle(),
  activate_kw=activate_kw
)
change_request.submit()

if REQUEST is None:
  return change_request

return change_request.Base_redirect()
