"""This script is called on the Invoice after the delivery builder has created
the new Invoice.
"""
from Products.ERP5Type.Message import translateString
from DateTime import DateTime
if related_simulation_movement_path_list is None:
  raise RuntimeError('related_simulation_movement_path_list is missing. Update ERP5 Product.')

invoice = context
price_currency = invoice.getPriceCurrency()
if invoice.getResource() != price_currency:
  invoice.setResource(price_currency)

if invoice.getPaymentMode("") == "":
  invoice.setPaymentModeValue(invoice.getPortalObject().portal_categories.payment_mode.payzen)

causality_list = []
min_start_date = None
max_stop_date = None
for line in invoice.objectValues():
  related_delivery = line.getDeliveryRelatedValue()
  if related_delivery is not None:
    root_applied_rule = related_delivery.getRootAppliedRule()
    if root_applied_rule is not None:
      causality = root_applied_rule.getCausality()
      if causality is not None and causality not in causality_list:
        causality_list.append(causality)

  if min_start_date is None:
    min_start_date = line.getStartDate()
  elif line.getStartDate() < min_start_date:
    min_start_date = line.getStartDate()

  if max_stop_date is None:
    max_stop_date = line.getStopDate()
  elif line.getStopDate() > max_stop_date:
    max_stop_date = line.getStopDate()

if context.getStartDate() is None:
  if min_start_date is None:
    min_start_date = DateTime().earliestTime()
  context.setStartDate(min_start_date)

  if max_stop_date is None:
    if min_start_date is not None:
      max_stop_date = min_start_date
    else:
      max_stop_date = DateTime().earliestTime()
  context.setStopDate(max_stop_date)


comment = translateString('Initialised by Delivery Builder.')

if invoice.getCausalityState() == 'draft':
  invoice.startBuilding(comment=comment)

if invoice.portal_workflow.isTransitionPossible(invoice, 'plan'):
  invoice.plan(comment=comment)
if invoice.portal_workflow.isTransitionPossible(invoice, 'confirm'):
  invoice.confirm(comment=comment)

invoice.setCausalityList(causality_list)

invoice.startBuilding(comment=comment)
