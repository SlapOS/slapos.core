"""This script is called on the Invoice after the delivery builder has created
the new Invoice.
"""
from Products.ERP5Type.Message import translateString
from DateTime import DateTime
if related_simulation_movement_path_list is None:
  raise RuntimeError, 'related_simulation_movement_path_list is missing. Update ERP5 Product.'

invoice = context
price_currency = invoice.getPriceCurrency()
if invoice.getResource() != price_currency:
  invoice.setResource(price_currency)
if invoice.getPaymentMode("") == "":
  invoice.setPaymentModeValue(invoice.getPortalObject().portal_categories.payment_mode.payzen)
comment = translateString('Initialised by Delivery Builder.')
if invoice.portal_workflow.isTransitionPossible(invoice, 'plan'):
  invoice.plan(comment=comment)
if invoice.portal_workflow.isTransitionPossible(invoice, 'confirm'):
  invoice.confirm(comment=comment)


causality_list = []
for line in invoice.objectValues():
  related_delivery = line.getDeliveryRelatedValue()
  if related_delivery is not None:
    root_applied_rule = related_delivery.getRootAppliedRule()
    if root_applied_rule is not None:
      causality = root_applied_rule.getCausality()
      if causality is not None and causality not in causality_list:
        causality_list.append(causality)

invoice.setCausalityList(causality_list)

invoice.startBuilding(comment=comment)
