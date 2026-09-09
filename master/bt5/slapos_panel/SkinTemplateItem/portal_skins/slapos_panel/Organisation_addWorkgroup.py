portal = context.getPortalObject()

resource = portal.restrictedTraverse("service_module/slapos_virtual_master_subscription")
buyer = context

# Using a temp object lead to security issue
# Use the current user instead to create temp service
if temp_customer is None:
  # The temp_customer parameter is only used in test
  # Not very elegant...
  temp_customer = portal.portal_membership.getAuthenticatedMember().getUserValue()

# create the project
temp_project = portal.project_module.newContent(
  portal_type='Project',
  destination_value=temp_customer,
  title=title,
  temp_object=True
)

currency_value = portal.restrictedTraverse(price_currency)

# create the subscription request, which will lead to the Open Order
try:
  temp_subscription_request = resource.Resource_createSubscriptionRequest(temp_customer, [], temp_project, currency_value=currency_value, temp_object=True)
except AssertionError as e:
  if batch:
    raise
  return context.Base_redirect(
    keep_items={
      'portal_status_level': 'error',
      'portal_status_message': str(e)
    },
  )

# Search for the root trade condition, defining how project are sold
specialise_value = temp_subscription_request.getSpecialiseValue(portal_type="Sale Trade Condition")

workgroup = portal.workgroup_module.newContent(
  portal_type="Workgroup",
  title=title,
  activate_kw=activate_kw
)
workgroup.validate()

# Create a trade condition defining how workgroup will pay for new project
# this trade condition will be later used to create instance trade condition per project
# XXX Copy/Pasted from Organisation_claimSlaposSubscriptionRequest
sale_trade_condition = portal.sale_trade_condition_module.newContent(
  portal_type='Sale Trade Condition',
  specialise_value=specialise_value,
  title='%s for %s' % (specialise_value.getTitle(), workgroup.getTitle()),
  destination_value=workgroup,
  destination_section_value=buyer,
  source_project=specialise_value.getSourceProject(),
  price_currency=specialise_value.getPriceCurrency(),
  trade_condition_type=specialise_value.getTradeConditionType(),
  activate_kw=activate_kw
)
sale_trade_condition.SaleTradeCondition_createSaleTradeConditionChangeRequestToValidate(activate_kw=activate_kw)

if batch:
  return workgroup
return workgroup.Base_redirect()
