"""return a list of invoices with the following attributes:
 - payment_request_uid: the uid of the invoice, we consider that payment request is the invoice.
 - total_price: the amount left to pay for this invoice
 - getTotalPrice: the original amount of this invoice.
 Arguments:
 - at_date (default None)
"""
portal = context.getPortalObject()

params = dict()

if at_date:
  params['at_date'] = at_date

params['grouping_reference'] = None

object_list = []

for (idx, brain) in enumerate(portal.portal_simulation.getInventoryList(
    mirror_section_uid=context.getUid(),
    simulation_state=('stopped', 'delivered'),
    node_uid=[x.uid for x in context.Base_getReceivableAccountList()] or -1,
    **params )):

  # XXX rewrap inventory list brain because they don't have a valid "uid" and cannot be used
  # directly in listbox. We should probably add support for this in getInventoryList instead
  # of this hack

  # XXX In our case, this hould be always None.
  payment_request_uid = brain.payment_request_uid
  if not payment_request_uid:
    payment_request_uid = brain.getObject().getExplanationUid()
  payment_request = portal.portal_catalog.getObject(uid=payment_request_uid)
  object_list.append(payment_request.asContext(
                section_uid=brain.section_uid,
                payment_request_uid=payment_request_uid,
                node_uid=brain.node_uid,
                node_relative_url=brain.node_relative_url,
                total_price=brain.total_price,
                uid='new_%s' % idx,))

return object_list
