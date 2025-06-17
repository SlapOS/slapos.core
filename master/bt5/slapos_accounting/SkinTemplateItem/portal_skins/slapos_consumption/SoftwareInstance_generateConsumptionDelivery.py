from zExceptions import Unauthorized
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance = context

assert instance.getAggregateValue(portal_type='Compute Partition') is not None
assert instance.getValidationState() == 'validated'



def storeWorkflowComment(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(
    ob=document,
    name='comment',
    wf_id='edit_workflow')
  if last_workflow_item != comment:
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

now = DateTime()


query_list = [
  Query(portal_type='Consumption Delivery'),
  Query(simulation_state='delivered'),
  Query(strict_causality_uid = instance.getUid()),
  Query(**{'delivery.start_date': {'query':now, 'range': 'ngt'}}),
  Query(**{'delivery.stop_date': {'query':now, 'range': 'nlt'}})
]


if portal.portal_catalog.getResultValue(
  query=ComplexQuery(logical_operator='AND', *query_list)
):
  return
# check accounting period of project
project = instance.getFollowUpValue(portal_type='Project')

# XX do we have multi open sale order line ??
open_sale_order_line = project.getAggregateRelatedValue(portal_type='Open Sale Order Line')
open_sale_order = open_sale_order_line.getParentValue()

project_stop_date = open_sale_order.getStopDate()
project_start_date = open_sale_order.getStartDate()
# we set a valide stop date, but it's already expired
if (project_stop_date > project_start_date) and project_stop_date < now:
  return


software_product, _, software_type = instance.InstanceTree_getSoftwareProduct()
resource_vcl = []
if software_product is not None:
  resource_vcl = [
    'software_type/%s' % software_type.getRelativeUrl()
  ]
else:
  storeWorkflowComment(instance, 'Can not find a matching Service to generate the Consumption Delivery')
  return

destination_value = project.getDestinationValue(portal_type="Person")
if destination_value is None:
  storeWorkflowComment(instance, 'Can not find the person to contact to generate the Consumption Delivery')
  return

line = open_sale_order.objectValues(portal_type='Open Sale Order Line')[0]
if line.getVariationCategoryList():
  cell = line.objectValues(portal_type='Open Sale Order Cell')[0]
  hosting_subscription = cell.getAggregateValue(portal_type='Hosting Subscription')
else:
  hosting_subscription = line.getAggregateValue(portal_type='Hosting Subscription')

stop_date = project_start_date
start_date = project_start_date

while stop_date < now:
  start_date = stop_date
  stop_date = hosting_subscription.getNextPeriodicalDate(stop_date)

tmp_sale_order = portal.portal_trash.newContent(
  portal_type='Sale Order',
  temp_object=True,
  trade_condition_type='virtual_master',
  start_date=start_date,
  stop_date = stop_date,
  destination_value=destination_value,
  source_project_value=project,
  #price_currency_value=currency_value  XXX
  ledger_value=portal.portal_categories.ledger.automated
)
tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)


if tmp_sale_order.getSpecialise(None) is None:
  raise AssertionError('Can not find a trade condition to generate the Consumption Delivery')

if tmp_sale_order.getTradeConditionType() != tmp_sale_order.getSpecialiseValue().getTradeConditionType():
  raise AssertionError('Unexpected different trade_condition_type: %s %s' % (tmp_sale_order.getTradeConditionType(), tmp_sale_order.getSpecialiseValue().getTradeConditionType()))



# If no accounting is needed, no price is expected
if (tmp_sale_order.getSourceSection(None) == tmp_sale_order.getDestinationSection(None)) or \
  (tmp_sale_order.getSourceSection(None) is None):
  price = 0

else:
  # Add line
  tmp_order_line = tmp_sale_order.newContent(
    portal_type='Sale Order Line',
    temp_object=True,
    resource_value=software_product,
    variation_category_list=resource_vcl,
    quantity_unit=software_product.getQuantityUnit(),
    base_contribution_list=software_product.getBaseContributionList(),
    use=software_product.getUse(),
    quantity=1
  )

  if resource_vcl:
    base_id = 'movement'
    cell_key = list(tmp_order_line.getCellKeyList(base_id=base_id))[0]
    tmp_order_cell = tmp_order_line.newCell(
      base_id=base_id,
      portal_type='Sale Order Cell',
      temp_object=True,
      *cell_key
    )

    tmp_order_cell.edit(
      mapped_value_property_list=['price','quantity'],
      quantity=1,
      predicate_category_list=cell_key,
      variation_category_list=cell_key
    )
    price = tmp_order_cell.getPrice() or 0
  else:
    price = tmp_order_line.getPrice() or 0


  # but if accounting is needed, we expect a price
  if not price:
    raise AssertionError('Can not find a price to generate the Consumption Delivery (%s)' % tmp_sale_order.getSpecialiseValue())

consumption_delivery = portal.consumption_delivery_module.newContent(
  portal_type="Consumption Delivery",
  source_value=tmp_sale_order.getSourceValue(),
  source_section_value=tmp_sale_order.getSourceSectionValue(),
  source_decision_value=tmp_sale_order.getSourceDecisionValue(),
  destination_value=tmp_sale_order.getDestinationValue(),
  destination_section_value=tmp_sale_order.getDestinationSectionValue(),
  destination_decision_value=tmp_sale_order.getDestinationDecisionValue(),
  specialise_value=tmp_sale_order.getSpecialiseValue(),
  source_project_value=tmp_sale_order.getSourceProjectValue(),
  destination_project_value=tmp_sale_order.getDestinationProjectValue(),
  ledger_value=tmp_sale_order.getLedgerValue(),
  start_date = tmp_sale_order.getStartDate(),
  stop_date = tmp_sale_order.getStopDate(),
  price_currency_value=tmp_sale_order.getPriceCurrencyValue(),
)

consumption_deliery_line = consumption_delivery.newContent(
  portal_type='Consumption Delivery Line',
  resource_value=software_product,
  variation_category_list=resource_vcl,
  quantity_unit=software_product.getQuantityUnit(),
  base_contribution_list=software_product.getBaseContributionList(),
  use=software_product.getUse(),
  quantity=1
)

if resource_vcl:
  base_id = 'movement'
  cell_key = list(consumption_deliery_line.getCellKeyList(base_id=base_id))[0]
  consumption_deliery_cell = consumption_deliery_line.newCell(
    base_id=base_id,
    portal_type='Consumption Delivery Cell',
    *cell_key
  )

  consumption_deliery_cell.edit(
    mapped_value_property_list=['price','quantity'],
    quantity=1,
    price = price,
    predicate_category_list=cell_key,
    variation_category_list=cell_key
  )
else:
  consumption_deliery_line.edit(price = price)

consumption_delivery.Delivery_fixBaseContributionTaxableRate()
consumption_delivery.Base_checkConsistency()
consumption_delivery.setCausalityValue(instance)
consumption_delivery.confirm()
consumption_delivery.start()
consumption_delivery.stop()
consumption_delivery.deliver()
consumption_delivery.startBuilding()
return consumption_delivery
