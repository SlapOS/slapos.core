from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

state = context.getSimulationState()
portal = context.getPortalObject()
entity = context.getDestinationDecisionValue(portal_type=portal.getPortalEntityTypeList())
if (state not in ('suspended', 'validated')) or \
   (entity is None):
  return

if not entity.Entity_hasOutstandingAmount(
    ledger_uid=portal.portal_categories.ledger.automated.getUid()):
  context.invalidate(comment="Automatically disabled as balance is ok")
