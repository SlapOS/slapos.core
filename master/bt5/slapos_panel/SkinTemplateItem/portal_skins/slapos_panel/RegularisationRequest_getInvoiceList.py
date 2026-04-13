portal = context.getPortalObject()

entity_url = context.getDestination()
if not entity_url:
  return []

entity = portal.restrictedTraverse(entity_url)
ledger_uid = portal.portal_categories.ledger.automated.getUid()

# Get receivable account UIDs
receivable_uid_list = [x.uid for x in portal.Base_getReceivableAccountList()]
if not receivable_uid_list:
  return []

# Find unpaid invoice UIDs: query stock for receivable lines without
# grouping_reference (not lettered = not paid), then extract parent invoice UIDs.
# Note: we cannot use Entity_getOutstandingAmountList here because it uses
# group_by_payment_request=True which merges invoices when payment_request_uid
# is NULL in the stock table, losing individual invoice UIDs.
unpaid_uid_set = set()
for brain in portal.portal_simulation.getInventoryList(
    mirror_section_uid=entity.getUid(),
    simulation_state=['stopped', 'delivered'],
    node_uid=receivable_uid_list,
    grouping_reference=None,
    ledger_uid=ledger_uid,
    portal_type=portal.getPortalAccountingMovementTypeList(),
):
  unpaid_uid_set.add(brain.getObject().getExplanationUid())

if not unpaid_uid_set:
  return []

kw.setdefault('simulation_state', ['stopped', 'delivered'])
kw.setdefault('ledger__uid', ledger_uid)
kw['entity'] = entity_url
kw['uid'] = list(unpaid_uid_set)
kw.setdefault('sort_on', [('operation_date', 'descending')])

# Call on accounting_module so that searchFolder uses the right scope
return portal.accounting_module.AccountingTransactionModule_getAccountingTransactionList(
  from_date=from_date,
  to_date=to_date,
  stat=stat,
  **kw
)
