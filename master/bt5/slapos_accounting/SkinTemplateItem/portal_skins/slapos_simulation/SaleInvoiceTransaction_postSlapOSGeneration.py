"""This script is called on the Invoice after the delivery builder has created
the new Invoice.
"""
from Products.ERP5Type.Message import translateString
from DateTime import DateTime

portal = context.getPortalObject()

if related_simulation_movement_path_list is None:
  raise RuntimeError('related_simulation_movement_path_list is missing. Update ERP5 Product.')

invoice = context
price_currency = invoice.getPriceCurrency()
if invoice.getResource() != price_currency:
  invoice.setResource(price_currency)

# Extend the invoice causality with the parent simulation movement explanation
# usually, Sale Packing List
causality_list = invoice.getCausalityList()
for simulation_movement in related_simulation_movement_path_list:
  simulation_movement = portal.restrictedTraverse(simulation_movement)
  if not simulation_movement.getExplanation().startswith(invoice.getRelativeUrl()):
    # Beware, the simulation movement may be not used to build the invoice
    # related_simulation_movement_path_list is the movement_list used by the builder
    continue
  applied_rule = simulation_movement.getParentValue()
  if applied_rule.getParentId() != 'portal_simulation':
    causality = applied_rule.getParentValue().getExplanationValue()
    if causality is not None:
      causality = causality.getRelativeUrl()
      if causality not in causality_list:
        causality_list.append(causality)
invoice.setCausalityList(causality_list)

# Link the Invoice to the original Deposit payment
# this allow the invoice and payment to be automatilly grouped (lettering)
if invoice.getCausality(None) is not None:
  new_causality = invoice.getCausalityValue()
  original_payment = new_causality.getCausalityValue(None, portal_type="Payment Transaction")
  if original_payment is not None:
    original_payment.setCausalityList(original_payment.getCausalityList() + [invoice.getRelativeUrl()])


comment = translateString('Initialised by Delivery Builder.')

if invoice.getCausalityState() == 'draft':
  invoice.startBuilding(comment=comment)

if invoice.portal_workflow.isTransitionPossible(invoice, 'plan'):
  invoice.plan(comment=comment)
if invoice.portal_workflow.isTransitionPossible(invoice, 'confirm'):
  invoice.confirm(comment=comment)


invoice.startBuilding(comment=comment)
