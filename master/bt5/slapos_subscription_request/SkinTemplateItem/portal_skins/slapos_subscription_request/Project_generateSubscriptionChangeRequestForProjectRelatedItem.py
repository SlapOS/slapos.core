from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, NegatedQuery
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if activate_kw is None:
  activate_kw = {}

project = context
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
  aggregate__portal_type=['Compute Node'],
  source_project__uid=project.getUid(),
  destination__uid=NegatedQuery(SimpleQuery(destination__uid=project.getDestinationUid())),
  validation_state='validated',

  method_id='OpenSaleOrderCell_generateSubscriptionChangeRequestForProjectRelatedItem',
  method_kw={'activate_kw': activate_kw},
  activate_kw=activate_kw
)
