portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop verification if there are too much tickets
  return

monitor_disabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/disabled", None)

from Products.ZSQLCatalog.SQLCatalog import Query, NegatedQuery

portal.portal_catalog.searchAndActivate(
    portal_type='Hosting Subscription',
    validation_state='validated',
    default_monitor_scope_uid = NegatedQuery(Query(default_monitor_scope_uid=monitor_disabled_category.getUid())),
    method_id='HostingSubscription_checkSoftwareInstanceState',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
