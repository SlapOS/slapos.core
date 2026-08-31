from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_request = context
portal = context.getPortalObject()

if subscription_request.getSimulationState() != 'submitted':
  return

workgroup = subscription_request.getDestinationSectionValue(portal_type='Workgroup')
project = subscription_request.getSourceProjectValue(portal_type='Project')
assert workgroup is not None
assert project is not None

# First, check if there is/was any Trade Condition for this workgroup/project ever created
# If any, do nothing
existing_trade_condition = portal.portal_catalog.getResultValue(
  portal_type='Sale Trade Condition',
  destination__uid=workgroup.getUid(),
  source_project__uid=project.getUid()
)
if existing_trade_condition is not None:
  return

# Then, look for the project trade condition linked to this workgroup
# (created when the workgroup is created normally)
# We will reuse the same Organisation destination section
# create the project
temp_project = portal.project_module.newContent(
  portal_type='Project',
  destination_value=workgroup,
  title=workgroup.getTitle(),
  temp_object=True
)
currency_value = subscription_request.getPriceCurrencyValue()
resource = portal.restrictedTraverse("service_module/slapos_virtual_master_subscription")
try:
  temp_project_subscription_request = resource.Resource_createSubscriptionRequest(workgroup, [], temp_project, currency_value=currency_value, temp_object=True)
except AssertionError:
  return
organisation = temp_project_subscription_request.getDestinationSectionValue(portal_type='Organisation')
if organisation is None:
  return

# Finally, create new Trade Condition
# XXX copy/paste from Organisation_claimSlaposSubscriptionRequest
current_trade_condition = subscription_request.getSpecialiseValue(portal_type='Sale Trade Condition')
new_sale_trade_condition = portal.sale_trade_condition_module.newContent(
  portal_type='Sale Trade Condition',
  specialise_value=current_trade_condition,
  title='%s for %s' % (current_trade_condition.getTitle(), workgroup.getTitle()),
  destination_value=workgroup,
  destination_section_value=organisation,
  source_project=current_trade_condition.getSourceProject(),
  price_currency=current_trade_condition.getPriceCurrency(),
  trade_condition_type=current_trade_condition.getTradeConditionType(),
  activate_kw=activate_kw
)
new_sale_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate(activate_kw=activate_kw)

for sql_result in portal.portal_catalog(
  portal_type='Subscription Request',
  simulation_state='submitted',
  destination_section__uid=workgroup.getUid(),
  source_project__uid=project.getUid(),
):
  submitted_subscription_request = sql_result.getObject()
  submitted_subscription_request.getResourceValue().Resource_createSubscriptionRequest(
    submitted_subscription_request.getDestinationValue(),
    # [software_type, software_release],
    submitted_subscription_request.getVariationCategoryList(),
    project,
    currency_value=submitted_subscription_request.getPriceCurrencyValue(),
    item_value=submitted_subscription_request.getAggregateValue(),
    causality_value=submitted_subscription_request,
    specialise_value=new_sale_trade_condition,
    portal_type='Subscription Change Request',
    activate_kw=activate_kw
  )

return new_sale_trade_condition
