"""return a list of invoices with the following attributes:
 - payment_request_uid: the uid of the invoice
 - node_relative_url : the url of the account ( if group_by_node=True is passed ).
 - total_price: the amount left to pay for this invoice
 - getTotalPrice: the original amount of this invoice.
 Arguments:
 - group_by_node (default True)
  If you pass group_by_node=False you have a list of all invoices,
  without the breakdown by account but if you pass group_by_node=True,
  you have on line for each account.
  To display to the user the list of invoices he has to pay, pass group_by_node=False,
  to create a list to pass to Entity_createPaymentTransaction, use group_by_node=True.
 - at_date (default None)
 - include_planned (default True)
  In current configuration, planned transactions, are used only in Payment Transactions for invoices of non-debitable customers.
  If you pass include_planned=True, you will get only unpaid invoices for which payment deadline is past
  If you pass include_planned=False, you will get all unpaid invoices, also those for which payment deadline is not past
"""

from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
portal = context.getPortalObject()

params = dict()

if at_date:
  params['at_date'] = at_date
  params['grouping_query'] = ComplexQuery(
      SimpleQuery(grouping_reference=None),
      SimpleQuery(grouping_date=at_date, comparison_operator=">"),
      logical_operator="OR")
else:
  params['grouping_reference'] = None

object_list = []

if include_planned:
  simulation_state_tuple = ('stopped', 'delivered', 'planned', 'confirmed', 'started')
else:
  simulation_state_tuple = ('stopped', 'delivered')

if section_uid is None:
  params['group_by_mirror_section'] = True
else:
  params['section_uid'] = section_uid

if resource_uid is None:
  params['group_by_resource'] = True
else:
  params['resource_uid'] = resource_uid

if ledger_uid is None:
  params['group_by_ledger'] = True
else:
  params['ledger_uid'] = ledger_uid

for (idx, brain) in enumerate(portal.portal_simulation.getInventoryList(
    mirror_section_uid=context.getUid(),
    simulation_state=simulation_state_tuple,
    group_by_payment_request=True,
    group_by_node=group_by_node,
    node_uid=[x.uid for x in context.Base_getReceivableAccountList()] or -1,
    **params )):

  # XXX rewrap inventory list brain because they don't have a valid "uid" and cannot be used
  # directly in listbox. We should probably add support for this in getInventoryList instead
  # of this hack

  payment_request_uid = brain.payment_request_uid
  if not payment_request_uid:
    payment_request_uid = brain.getObject().getExplanationUid()
  payment_request = portal.portal_catalog.getObject(uid=payment_request_uid)
  object_list.append(payment_request.asContext(
                section_uid=brain.section_uid,
                resource_uid=brain.resource_uid,
                ledger_uid=brain.ledger_uid,
                payment_request_uid=payment_request_uid,
                node_uid=brain.node_uid,
                node_relative_url=brain.node_relative_url,
                total_price=brain.total_price,
                uid='new_%s' % idx,))

return object_list
