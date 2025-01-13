from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

state = context.getSimulationState()
entity = context.getDestinationDecisionValue(portal_type=["Person", "Organisation"])
if (state not in ('suspended', 'validated')) or \
   (entity is None):
  return

if not entity.Entity_hasOutstandingAmount(ledger_uid=context.getPortalObject().portal_categories.ledger.automated.getUid()):
  context.invalidate(comment="Automatically disabled as balance is ok")
