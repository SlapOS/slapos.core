from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
open_internal_order = context
assert open_internal_order.getValidationState() == 'validated'

open_internal_line_list = open_internal_order.contentValues(portal_type='Open Internal Order Line')
assert len(open_internal_line_list) == 1
open_internal_line = open_internal_line_list[0]

assert service != open_internal_line.getResource()

edit_kw = {
  'resource': service,
  'aggregate': open_internal_line.getAggregate(portal_type=['Compute Node', 'Software Instance', 'Slave Instance'])
}
for edit_key in [
  'destination',
  'destination_section',
  'destination_decision',
  'destination_project',
  # 'resource',
  # 'variation_category_list',
  # 'quantity_unit',
  'quantity',
  'ledger',
  'source',
  'source_section',
  'source_project',
  'price_currency',
  'price'
  'specialise'
]:
  edit_kw[edit_key] = open_internal_line.getProperty(edit_key)
consumption_change_request = portal.consumption_change_request_module.newContent(
  portal_type='Consumption Change Request',
  causality_value=open_internal_order,
  **edit_kw
)
consumption_change_request.Base_checkConsistency()
consumption_change_request.submit()

open_internal_order.reindexObject(activate_kw=activate_kw)
consumption_change_request.reindexObject(activate_kw=activate_kw)

# Prevent concurrent transactions which could create the Open Consumption Order
open_internal_order.serialize()

if batch:
  return consumption_change_request
return consumption_change_request.Base_redirect()
