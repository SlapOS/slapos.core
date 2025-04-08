portal = context.getPortalObject()
activate_kw = {'tag': tag, 'priority': 2}
account = portal.Base_getAccountForUse('asset_receivable_subscriber')

payment_transaction_set = set()

for sql_movement in portal.portal_simulation.getMovementHistoryList(
  parent_portal_type='Payment Transaction',
  node_uid=account.getUid(),
  ledger_uid=portal.portal_categories.ledger.automated.getUid(),
  portal_type=portal.getPortalAccountingMovementTypeList(),
  grouping_reference=None,
  simulation_state=['stopped', 'delivered'],
):
  movement = sql_movement.getObject()
  payment_transaction = movement.getParentValue()
  if payment_transaction not in payment_transaction_set:
    # Prevent generating conflicts on transaction with multiple lines
    movement.activate(**activate_kw).AccountingTransactionLine_createMirrorPaymentTransactionToGroupSaleInvoice(activate_kw=activate_kw)
    payment_transaction_set.add(payment_transaction)

context.activate(after_tag=tag).getId()
