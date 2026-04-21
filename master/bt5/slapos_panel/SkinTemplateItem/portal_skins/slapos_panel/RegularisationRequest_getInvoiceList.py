portal = context.getPortalObject()

entity = context.getDestinationValue()
if not entity:
  return []

ledger_uid = portal.portal_categories.ledger.automated.getUid()

# Two-call pattern: first call (without section_uid/resource_uid) returns
# aggregates grouped by (mirror_section, resource). The second call, made per
# aggregate with explicit section_uid and resource_uid, disables that grouping
# and returns one entry per individual unpaid invoice.
result = []
for aggregate in entity.Entity_getOutstandingAmountList(
    ledger_uid=ledger_uid,
    group_by_node=False,
):
  result.extend(entity.Entity_getOutstandingAmountList(
      ledger_uid=ledger_uid,
      section_uid=aggregate.section_uid,
      resource_uid=aggregate.resource_uid,
      group_by_node=False,
  ))
return result
