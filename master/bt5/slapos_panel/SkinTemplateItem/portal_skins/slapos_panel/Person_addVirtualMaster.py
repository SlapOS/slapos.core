portal = context.getPortalObject()

# Normalise with SubscriptionRequest_createOpenSaleOrder
from erp5.component.module.DateUtils import getClosestDate, addToDate
effective_date = getClosestDate(target_date=DateTime(), precision='day')
while effective_date.day() >= 29:
  effective_date = addToDate(effective_date, to_add={'day': -1})

resource = portal.restrictedTraverse("service_module/slapos_virtual_master_subscription")
customer = context

# create the project
project = portal.project_module.newContent(
  portal_type='Project',
  destination_value=customer,
  title=title,
  activate_kw=activate_kw
)
project.validate()

currency_value = portal.restrictedTraverse(price_currency)

# create the subscription request, which will lead to the Open Order
try:
  subscription_request = resource.Resource_createSubscriptionRequest(customer, [], project, currency_value=currency_value)
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
subscription_request.reindexObject(activate_kw=activate_kw)

# XXX How to specify the trade condition containing the currency and trade model lines?
specialise_value = subscription_request.getSpecialiseValue(portal_type="Sale Trade Condition")
while ((specialise_value is not None) and
    (len(specialise_value.contentValues(portal_type="Trade Model Line")) == 0)):
  specialise_value = specialise_value.getSpecialiseValue(portal_type="Sale Trade Condition")

if ((specialise_value is None) or
    (len(specialise_value.contentValues(portal_type="Trade Model Line")) == 0)):
  raise ValueError('Could not find a Trade Condition with Trade Model Line')

# and create default assignments for the user
# who can manage compute nodes and create instances
customer.newContent(
  portal_type='Assignment',
  title="Manager for %s" % project.getReference(),
  destination_project_value=project,
  function='production/manager',
  activate_kw=activate_kw
).open()
customer.newContent(
  portal_type='Assignment',
  title="Client for %s" % project.getReference(),
  destination_project_value=project,
  function='customer',
  activate_kw=activate_kw
).open()

# Compute Node trade condition
if is_compute_node_payable:
  source_section_value = subscription_request.getSourceSectionValue(
    default=subscription_request.getSourceValue(default=None, portal_type='Organisation'),
    portal_type='Organisation'
  )
  if source_section_value is None:
    raise AssertionError('No source section found to generate the invoices')
else:
  source_section_value = None

destination_section_value = None
if subscription_request.getDestinationSectionUid() != customer.getUid():
  destination_section_value = subscription_request.getDestinationSectionValue()
sale_trade_condition = portal.sale_trade_condition_module.newContent(
  portal_type="Sale Trade Condition",
  reference='%s-ComputeNode' % project.getReference(),
  trade_condition_type="compute_node",
  specialise_value=specialise_value,
  source_project_value=project,
  source_value=subscription_request.getSourceValue(),
  source_section_value=source_section_value,
  #source_payment_value=seller_bank_account,
  # The person will pay for all compute node
  destination_section_value=destination_section_value,
  price_currency_value=currency_value,
  effective_date=effective_date,
  activate_kw=activate_kw
)
sale_trade_condition.validate()

# Instance Tree trade condition
if is_instance_tree_payable:
  source_section_value = subscription_request.getSourceSectionValue(
    default=subscription_request.getSourceValue(default=None, portal_type='Organisation'),
    portal_type='Organisation'
  )
  if source_section_value is None:
    raise AssertionError('No source section found to generate the invoices')
else:
  source_section_value = None
sale_trade_condition = portal.sale_trade_condition_module.newContent(
  portal_type="Sale Trade Condition",
  reference='%s-InstanceTree' % project.getReference(),
  trade_condition_type="instance_tree",
  specialise_value=specialise_value,
  source_project_value=project,
  source_value=subscription_request.getSourceValue(),
  source_section_value=source_section_value,
  #source_payment_value=seller_bank_account,
  price_currency_value=currency_value,
  effective_date=effective_date,
  activate_kw=activate_kw
)
sale_trade_condition.validate()

if is_compute_node_payable or is_instance_tree_payable:
  # Create a draft sale supply to buy nodes / instances
  # Sale Manager must manually enter the prices on it and validate
  sale_supply = portal.sale_supply_module.newContent(
    portal_type="Sale Supply",
    title="Project Prices for %s" % project.getReference(),
    source_project_value=project,
    price_currency_value=currency_value,
    start_date_range_min=sale_trade_condition.getEffectiveDate()
  )
  if is_compute_node_payable:
    sale_supply.newContent(
      portal_type="Sale Supply Line",
      resource="service_module/slapos_compute_node_subscription"
    )

if batch:
  return project
return project.Base_redirect()
