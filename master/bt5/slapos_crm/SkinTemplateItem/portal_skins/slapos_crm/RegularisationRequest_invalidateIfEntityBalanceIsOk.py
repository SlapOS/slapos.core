from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

state = context.getSimulationState()
portal = context.getPortalObject()
if (state not in ('suspended', 'validated')):
  return

entity = context.getDestinationSectionValue(portal_type=portal.getPortalEntityTypeList())
actor = context.getDestination(portal_type=portal.getPortalActorTypeList())
currency = context.getPriceCurrency()
if (entity is None) or \
   (actor is None) or \
   (currency is None):
  context.invalidate(comment="Missing informations.")
  return

seen = False
for outstanding_invoice in entity.Entity_getOutstandingInvoiceList():
  if (actor == outstanding_invoice.getDestination()) and (currency == outstanding_invoice.getPriceCurrency()):
    seen = True
if not seen:
  context.invalidate(comment="Automatically disabled as balance is ok")
