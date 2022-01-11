item = context
portal = context.getPortalObject()

if (item.getPortalType() == 'Instance Tree') and (item.getSlapState() == "destroy_requested"):
  return 'todestroy'

# If no open order, subscription must be approved
open_sale_order_movement_list = portal.portal_catalog(
  portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
  aggregate__uid=item.getUid(),
  validation_state='validated',
  limit=1
)

if len(open_sale_order_movement_list) == 0:
  return "not_subscribed"

# Check if there are some ongoing Regularisation Requestion
# if so, return to_pay

return "subscribed"
