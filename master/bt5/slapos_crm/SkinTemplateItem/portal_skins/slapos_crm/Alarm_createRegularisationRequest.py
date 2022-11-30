portal = context.getPortalObject()

person_uid_list = []
for (_, brain) in enumerate(portal.portal_simulation.getInventoryList(
    simulation_state=('stopped', 'delivered'),
    parent_payment_mode_uid = [
      portal.portal_categories.payment_mode.payzen.getUid(),
      portal.portal_categories.payment_mode.wechat.getUid()],
    group_by_mirror_section=True,
    portal_type=portal.getPortalAccountingMovementTypeList(),
    node_uid=[x.uid for x in context.Base_getReceivableAccountList()],
    grouping_reference=None)):

  payment_request_uid = brain.payment_request_uid
  if not payment_request_uid:
    payment_request_uid = brain.getObject().getExplanationUid()

  payment_request = portal.portal_catalog.getObject(uid=payment_request_uid)
  section_uid = payment_request.getDestinationSectionUid(portal_type="Person")
  if section_uid is not None:
    person_uid_list.append(section_uid)

portal.portal_catalog.searchAndActivate(
      portal_type="Person", 
      validation_state="validated",
      uid=person_uid_list,
      method_id='Person_checkToCreateRegularisationRequest',
      activate_kw={'tag': tag}
      )
context.activate(after_tag=tag).getId()
