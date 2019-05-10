from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if uid is None:
  uid = context.getUid()

portal = context.getPortalObject()

order = portal.portal_catalog(
  uid=uid,
  select_dict={'indexation_timestamp': None})[0]

indexation_timestamp = order.indexation_timestamp

line_list = portal.portal_catalog(
  portal_type="Open Sale Order Line",
  parent_uid=uid,
  indexation_timestamp={'query': indexation_timestamp, 'range': 'nlt'},
  limit=1)

if len(line_list):
  order.getObject().activate().immediateReindexObject()
