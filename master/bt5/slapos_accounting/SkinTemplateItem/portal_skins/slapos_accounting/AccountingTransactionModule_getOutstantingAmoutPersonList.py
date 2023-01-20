portal = context.getPortalObject()
params = dict()

if at_date:
  params['at_date'] = at_date

if parent_portal_type:
  params['parent_portal_type'] = parent_portal_type

params['grouping_reference'] = None

object_list = []

for (_, brain) in enumerate(portal.portal_simulation.getInventoryList(
    group_by_mirror_section=True,
    simulation_state=('stopped', 'delivered'),
    node_uid=[x.uid for x in context.Base_getReceivableAccountList()] or -1,
    **params )):

  # XXX In our case, this hould be always None.
  payment_request_uid = brain.payment_request_uid
  if not payment_request_uid:
    payment_request_uid = brain.getObject().getExplanationUid()
  payment_request = portal.portal_catalog.getObject(uid=payment_request_uid)
  person = payment_request.getDestinationSectionValue(portal_type="Person")
  if person is not None:
    object_list.append(person)

return object_list
