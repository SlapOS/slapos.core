# Search by a trade condition that specialise to the root_trade_condition
# Which is user's specific.

# XXX This code is draft
portal = context.getPortalObject()
if root_trade_condition is None:
  return root_trade_condition


root_trade_condition_value = portal.restrictedTraverse(root_trade_condition)
trade_condition = portal.portal_catalog.ERP5Site_searchRelatedInheritedSpecialiseList(
  portal_type=root_trade_condition_value.getPortalType(),
  specialise_uid=root_trade_condition_value.getUid(),
  validation_state=root_trade_condition_value.getValidationState(),
  destination_section__uid=context.getUid()
)
if len(trade_condition) == 1:
  trade_condition = trade_condition[0].getObject()
elif len(trade_condition) == 0:
  trade_condition = None
else:
  raise NotImplementedError('Too many trade aggregated subscription trade condition for %s' % context.getRelativeUrl())

if trade_condition is not None:
  return trade_condition.getRelativeUrl()

return root_trade_condition
