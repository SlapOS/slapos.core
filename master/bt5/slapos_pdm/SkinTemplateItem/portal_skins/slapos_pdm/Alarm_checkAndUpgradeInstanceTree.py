from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery, SimpleQuery

portal = context.getPortalObject()
previous_run_date = context.Alarm_storeCurrentRunDateAndReturnPreviousRunDate(params)

search_kw = {"slapos_item.slap_state": ['start_requested', 'stop_requested']}

if previous_run_date is not None:
  # Gather recently modified Allocation Supply's projects
  # and only check them
  allocation_supply_list = portal.portal_catalog(
    portal_type='Allocation Supply',
    group_by_list=['destination_project_uid'],
    indexation_timestamp=SimpleQuery(
      indexation_timestamp=previous_run_date,
      comparison_operator=">="
    ),
  )
  search_kw['follow_up__uid'] = [x.getDestinationProjectUid() for x in allocation_supply_list] or [-1]

portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  validation_state = 'validated',
  # Do not try to upgrade instance tree created by Remote Node
  # as it will only lead to software release url inconsistency
  title=NegatedQuery(Query(title='\\_remote\\_%\\_%')),

  method_id = 'InstanceTree_createUpgradeDecision',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  # Put a really high value, as this alarm is not critical
  # And should not slow down others
  activate_kw = {'tag':tag, 'priority': 5},
  **search_kw
)

context.activate(after_tag=tag).getId()
