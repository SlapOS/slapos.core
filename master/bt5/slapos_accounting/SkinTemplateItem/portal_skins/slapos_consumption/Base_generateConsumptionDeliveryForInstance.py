from zExceptions import Unauthorized
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance = context

def storeWorkflowComment(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(
    ob=document,
    name='comment',
    wf_id='edit_workflow')
  if last_workflow_item != comment:
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

now = DateTime()


default_query_list = [
  Query(portal_type='Consumption Delivery'),
  Query(simulation_state='delivered'),
  Query(strict_causality_uid = instance.getUid())
]

# check accounting period of project
project = instance.getFollowUpValue(portal_type='Project')


# XX do we have multi open sale order line ??
open_sale_order_line = project.getAggregateRelatedValue(portal_type='Open Sale Order Line')
if not open_sale_order_line:
  return
open_sale_order = open_sale_order_line.getParentValue()
currency_value = open_sale_order.getPriceCurrencyValue()

project_stop_date = open_sale_order.getStopDate()
project_start_date = open_sale_order.getStartDate()
# we set a valide stop date, but it's already expired
if (project_stop_date > project_start_date) and project_stop_date < now:
  return now

consumption_service = instance.Instance_getConsumptionService()

subscriber_person_value = project.getDestinationValue(portal_type="Person")
if subscriber_person_value is None:
  storeWorkflowComment(instance, 'Can not find the person to contact to generate the Consumption Delivery')
  return

line = open_sale_order.objectValues(portal_type='Open Sale Order Line')[0]
if line.getVariationCategoryList():
  cell = line.objectValues(portal_type='Open Sale Order Cell')[0]
  hosting_subscription = cell.getAggregateValue(portal_type='Hosting Subscription')
else:
  hosting_subscription = line.getAggregateValue(portal_type='Hosting Subscription')

stop_date = context.getCreationDate()


price = None

while stop_date <= now:
  start_date = stop_date
  stop_date = hosting_subscription.getNextPeriodicalDate(stop_date)
  query_list = default_query_list[:]
  query_list.append(Query(**{'delivery.start_date': {'query':start_date, 'range': 'ngt'}}))
  query_list.append(Query(**{'delivery.stop_date': {'query':start_date, 'range': 'nlt'}}))
  if portal.portal_catalog.getResultValue(
    query=ComplexQuery(logical_operator='AND', *query_list)
  ):
    continue

  if price is None:
    trade_condition = open_sale_order.getSpecialiseValue(portal_type='Sale Trade Condition')
    tmp_sale_order = portal.portal_trash.newContent(
      portal_type='Sale Order',
      temp_object=True,
      start_date= project_start_date,
      source_project_value=project,
      destination_value=subscriber_person_value,
      price_currency_value=currency_value,
      ledger_value=portal.portal_categories.ledger.automated,
      specialise_value = trade_condition
    )

    tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)


    if tmp_sale_order.getSpecialise(None) is None:
      raise AssertionError('Can not find a trade condition to generate the Consumption Delivery')

    # If no accounting is needed, no price is expected
    if (tmp_sale_order.getSourceSection(None) == tmp_sale_order.getDestinationSection(None)) or \
      (tmp_sale_order.getSourceSection(None) is None):
      price = 0
    else:
      # Add line
      tmp_order_line = tmp_sale_order.newContent(
        portal_type='Sale Order Line',
        temp_object=True,
        resource_value=consumption_service,
        quantity_unit=consumption_service.getQuantityUnit(),
        base_contribution_list=consumption_service.getBaseContributionList(),
        use=consumption_service.getUse(),
        quantity=1
      )
      price = tmp_order_line.getPrice() or 0
      # but if accounting is needed, we expect a price
      if not price:
        raise AssertionError('Can not find a price to generate the Consumption Delivery (%s)' % tmp_sale_order.getSpecialise())

  consumption_delivery = portal.consumption_delivery_module.newContent(
    portal_type="Consumption Delivery",
    source_value=tmp_sale_order.getSourceValue(),
    source_section_value=tmp_sale_order.getSourceSectionValue(),
    source_decision_value=tmp_sale_order.getSourceDecisionValue(),
    destination_value=tmp_sale_order.getDestinationValue(),
    destination_section_value=subscriber_person_value,
    destination_decision_value=subscriber_person_value,
    specialise_value=tmp_sale_order.getSpecialiseValue(),
    destination_project_value=tmp_sale_order.getDestinationProjectValue(),
    ledger_value=tmp_sale_order.getLedgerValue(),
    start_date = start_date,
    stop_date = stop_date,
    price_currency_value=tmp_sale_order.getPriceCurrencyValue(),
  )

  consumption_deliery_line = consumption_delivery.newContent(
    portal_type='Consumption Delivery Line',
    resource_value=consumption_service,
    quantity_unit=consumption_service.getQuantityUnit(),
    base_contribution_list=consumption_service.getBaseContributionList(),
    use=consumption_service.getUse(),
    aggregate_value = tmp_sale_order.getSourceProjectValue(),
    quantity=1
  )

  consumption_deliery_line.edit(price = price)

  consumption_delivery.Delivery_fixBaseContributionTaxableRate()
  consumption_delivery.Base_checkConsistency()
  consumption_delivery.setCausalityValue(instance)
  consumption_delivery.confirm()
  consumption_delivery.start()
  consumption_delivery.stop()
  consumption_delivery.deliver()
  consumption_delivery.startBuilding()

return stop_date
