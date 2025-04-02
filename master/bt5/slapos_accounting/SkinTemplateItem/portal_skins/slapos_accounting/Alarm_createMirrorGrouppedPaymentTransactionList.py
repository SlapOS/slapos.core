portal = context.getPortalObject()
activate_kw = {'tag': tag, 'priority': 2}
account = portal.Base_getAccountForUse('asset_receivable_subscriber')

for sql_movement in portal.portal_simulation.getMovementHistoryList(
  parent_portal_type='Payment Transaction',
  node_uid=account.getUid(),
  ledger_uid=portal.portal_categories.ledger.automated.getUid(),
  portal_type=portal.getPortalAccountingMovementTypeList(),
  grouping_reference=None,
  simulation_state=['stopped', 'delivered'],
):
  movement = sql_movement.getObject()
  movement.activate(**activate_kw).AccountingTransactionLine_createMirrorPaymentTransactionToGroupSaleInvoice(activate_kw=activate_kw)

context.activate(after_tag=tag).getId()
