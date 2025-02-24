from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery

portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Instance Tree',
  validation_state = 'validated',
  # Do not try to upgrade instance tree created by Remote Node
  # as it will only lead to software release url inconsistency
  title=NegatedQuery(Query(title='_remote_%')),

  method_id = 'InstanceTree_createUpgradeDecision',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  activate_kw = {'tag':tag, 'priority': 2},
  **{"slapos_item.slap_state": ['start_requested', 'stop_requested']}
)

context.activate(after_tag=tag).getId()
