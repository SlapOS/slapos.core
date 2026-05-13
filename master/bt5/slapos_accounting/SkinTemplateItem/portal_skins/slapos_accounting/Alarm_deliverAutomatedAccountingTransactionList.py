from DateTime import DateTime

portal = context.getPortalObject()
now = DateTime()

for sql_result in portal.portal_catalog(
  parent_portal_type='Organisation',
  portal_type='Accounting Period',
  simulation_state='started',
):
  accounting_period = sql_result.getObject()
  handled_transaction_dict = {}

  from_date = accounting_period.getStartDate().earliestTime()
  at_date = accounting_period.getStopDate().latestTime()
  if (now < from_date) or (now < at_date):
    continue

  if len(accounting_period.checkConsistency()) != 0:
    continue

  movement_list = portal.portal_simulation.getMovementHistoryList(
    section_uid=accounting_period.getParentValue().getUid(),
    from_date=from_date,
    at_date=at_date,
    simulation_state='stopped',
    # We only consider accounting movements really using accounts as node.
    # There could be a line in stock table because the node is an organisation acquired
    # from parent invoice.
    node_uid=[node.uid for node in portal.portal_catalog(portal_type='Account')],
    portal_type=portal.getPortalAccountingMovementTypeList(),
    ledger_uid=portal.portal_categories.ledger.automated.getUid()
  )

  for movement in movement_list:
    transaction = movement.getParentValue()
    transaction_relative_url = transaction.getRelativeUrl()

    if transaction_relative_url in handled_transaction_dict:
      continue
    handled_transaction_dict[transaction_relative_url] = True

    if len(transaction.checkConsistency()) != 0:
      continue
    transaction.deliver(comment='Allow to close the accounting period %s' % accounting_period.getRelativeUrl())
    transaction.reindexObject(activate_kw={'tag': tag})

context.activate(after_tag=tag).getId()
