portal = context.getPortalObject()
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery

portal.portal_catalog.searchAndActivate(
  portal_type='Hosting Subscription',
  validation_state='validated',
  related_successor_but_with_different_title_than_catalog_title="%",
  successor_title=NegatedQuery(SimpleQuery(successor_title=None, comparison_operator='is')),
  method_id='HostingSubscription_assertSuccessor',
  activate_kw={'tag': tag})

context.activate(after_tag=tag).getId()
