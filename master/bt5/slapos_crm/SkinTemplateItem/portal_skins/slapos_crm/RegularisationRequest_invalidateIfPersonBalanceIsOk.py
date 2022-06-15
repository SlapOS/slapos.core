from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

state = context.getSimulationState()
person = context.getDestinationDecisionValue(portal_type="Person")
if (state not in ('suspended', 'validated')) or \
   (person is None):
  return

if not person.Entity_hasOutstandingAmount(ledger_uid=context.getPortalObject().portal_categories.ledger.automated.getUid()):
  context.invalidate(comment="Automatically disabled as balance is ok")
