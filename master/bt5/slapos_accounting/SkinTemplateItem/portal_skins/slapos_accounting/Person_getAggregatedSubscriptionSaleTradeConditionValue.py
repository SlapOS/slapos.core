# Search by a trade condition that specialise to the root_trade_condition
# Which is user's specific.

# XXX This code is draft
portal = context.getPortalObject()
if root_trade_condition is None:
  return root_trade_condition


root_trade_condition_value = portal.restrictedTraverse(root_trade_condition)
trade_condition = portal.portal_catalog.getResultValue(
  portal_type=root_trade_condition_value.getPortalType(),
  specialise__uid=root_trade_condition_value.getUid(),
  validation_state=root_trade_condition_value.getValidationState(),
  destination_section__uid=context.getUid()
)

if trade_condition is not None:
  return trade_condition.getRelativeUrl()

return root_trade_condition
