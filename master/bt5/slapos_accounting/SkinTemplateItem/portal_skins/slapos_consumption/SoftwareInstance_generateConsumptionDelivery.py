import six
from zExceptions import Unauthorized
from DateTime import DateTime
from Products.ZSQLCatalog.SQLCatalog import Query, ComplexQuery


if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance = context

assert instance.getAggregateValue(portal_type='Compute Partition') is not None
assert instance.getValidationState() == 'validated'

now = DateTime()


query_list = [
  Query(portal_type='Consumption Delivery'),
  Query(simulation_state='delivered'),
  Query(strict_causality_uid = instance.getUid()),
  Query(**{'delivery.start_date': {'query':now, 'range': 'ngt'}}),
  Query(**{'delivery.stop_date': {'query':now, 'range': 'nlt'}})
]


if portal.portal_catalog.getResultValue(
  query=ComplexQuery(logical_operator='AND', *query_list)
):
  return
# check accounting period of project
project = instance.getFollowUpValue(portal_type='Project')

# XX do we have multi open sale order line ??
open_sale_order_line = project.getAggregateRelatedValue(portal_type='Open Sale Order Line')
open_sale_order = open_sale_order_line.getParentValue()

project_stop_date = open_sale_order.getStopDate()
# we set a valide stop date, but it's already expired
if (project_stop_date > open_sale_order.getStartDate()) and project_stop_date < now:
  return


#XXXXXXX
