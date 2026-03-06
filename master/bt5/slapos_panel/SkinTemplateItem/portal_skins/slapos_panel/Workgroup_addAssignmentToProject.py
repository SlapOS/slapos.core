portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
workgroup = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

assert context.getPortalType() == 'Workgroup'

# Search for the matching item
sql_project_list = portal.portal_catalog(
  reference=reference,
  portal_type='Project',
  validation_state='validated',
  limit=2
)
if len(sql_project_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_project_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

project = sql_project_list[0].getObject()

# Used as base calculation only
resource = portal.restrictedTraverse("service_module/slapos_virtual_master_subscription")
currency_value = portal.restrictedTraverse(price_currency)

try:
  subscription_request = resource.Resource_createSubscriptionRequest(workgroup, [], project, currency_value=currency_value, temp_object=True)
except AssertionError as e:
  if batch:
    raise
  return context.Base_redirect(
    keep_items={
      'portal_status_level': 'error',
      'portal_status_message': str(e)
    },
    abort_transaction=True,
  )
specialise_value = subscription_request.getSpecialiseValue(portal_type="Sale Trade Condition")
while ((specialise_value is not None) and
    (len(specialise_value.contentValues(portal_type="Trade Model Line")) == 0)):
  specialise_value = specialise_value.getSpecialiseValue(portal_type="Sale Trade Condition")

# Create the assignment request
portal.assignment_request_module.newContent(
  portal_type='Assignment Request',
  destination_decision_value=workgroup,
  title="Client for %s" % project.getReference(),
  destination_project_value=project,
  function='customer',
  activate_kw=activate_kw
).submit()

# Now create the trade condition to the user
sale_trade_condition = portal.sale_trade_condition_module.newContent(
  portal_type="Sale Trade Condition",
  title='%s-InstanceTree-%s' % (project.getReference(), workgroup.getReference()),
  trade_condition_type="instance_tree",
  specialise_value=specialise_value,
  source_project_value=project,
  source_value=subscription_request.getSourceValue(),
  source_section_value=subscription_request.getSourceSectionValue(),
  destination_section_value=workgroup.getDestinationSectioValue(),
  destination_value=workgroup,
  price_currency_value=currency_value,
  activate_kw=activate_kw
)
sale_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate(activate_kw=activate_kw)

if batch:
  return workgroup
return workgroup.Base_redirect()
