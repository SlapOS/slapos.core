from Products.ZSQLCatalog.SQLCatalog import SimpleQuery

portal = context.getPortalObject()

activate_kw={'tag': tag, 'priority': 2}
previous_run_date = context.Alarm_storeCurrentRunDateAndReturnPreviousRunDate(params)

portal.portal_catalog.searchAndActivate(
  portal_type='Compute Partition',
  free_for_request=0,
  parent_portal_type='Remote Node',
  parent__validation_state='validated',
  method_id='ComputePartition_propagateRemoteNode',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  method_kw={
    "previous_run_date": previous_run_date,
    "activate_kw": activate_kw
  },
  activate_kw=activate_kw
)

if previous_run_date is not None:
  # In such case, the date criteria will only check compute partition
  # with recently modified instance
  # It is needed to search all _remote_ instances
  portal.portal_catalog.searchAndActivate(
    portal_type='Instance Tree',
    title='_remote_%',
    indexation_timestamp=SimpleQuery(
      indexation_timestamp=previous_run_date,
      comparison_operator=">="
    ),
    method_id='InstanceTree_propagateFromRemoteNode',
    method_kw={
      "activate_kw": activate_kw
    },
    activate_kw=activate_kw
  )

context.activate(after_tag=tag).getId()
