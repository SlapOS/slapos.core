portal = context.getPortalObject()
destination_decision_value = context

# Create a temp Sale Order to find the trade condition
now = DateTime()
module = portal.portal_trash
tmp_sale_order = module.newContent(
  portal_type='Sale Order',
  temp_object=True,
  trade_condition_type="ticket",
  start_date=now,
  destination_value=destination_decision_value,
  destination_decision_value=destination_decision_value,
  source_project=source_project,
  ledger_value=portal.portal_categories.ledger.automated
)
tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)
"""
if tmp_sale_order.getSpecialise(None) is None:
  raise AssertionError('Can not find a trade condition to generate the Support Request')
"""
resource = portal.restrictedTraverse(resource)
ticket = portal.getDefaultModule(portal_type).newContent(
  portal_type=portal_type,
  title=title,
  description=text_content,
  start_date=tmp_sale_order.getStartDate(),
  source=tmp_sale_order.getSource(),
  source_section=tmp_sale_order.getSourceSection(),
  source_project=tmp_sale_order.getSourceProject(),
  destination=tmp_sale_order.getDestination(),
  destination_section=tmp_sale_order.getDestinationSection(),
  destination_project=tmp_sale_order.getDestinationProject(),
  destination_decision=tmp_sale_order.getDestinationDecision(),
  specialise=tmp_sale_order.getSpecialise(),
  causality=causality,
  # Ensure resoure is Monitoring
  resource_value=resource,
  quantity_unit=resource.getQuantityUnit(),
  base_contribution_list=resource.getBaseContributionList(),
  use=resource.getUse(),
  quantity=1,
  price=0
)
ticket.submit(comment=comment)

return ticket
