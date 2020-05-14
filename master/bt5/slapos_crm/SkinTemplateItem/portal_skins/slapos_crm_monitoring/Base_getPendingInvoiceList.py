catalog = context.getPortalObject().portal_catalog
payment_list = catalog(
  portal_type='Payment Transaction',
  simulation_state=simulation_state,
  limit=limit
)

invoice_list = []
for payment in payment_list:
  if payment.getSimulationState() == simulation_state:
    invoice_list.extend(payment.getCausalityValueList(portal_type='Sale Invoice Transaction'))
return invoice_list
