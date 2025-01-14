portal = context.getPortalObject()

entity_uid_list = []
for (_, brain) in enumerate(portal.portal_simulation.getInventoryList(
    simulation_state=('stopped', 'delivered'),
    group_by_mirror_section=True,
    portal_type=portal.getPortalAccountingMovementTypeList(),
    node_uid=[x.uid for x in context.Base_getReceivableAccountList()] or -1,
    parent__ledger__uid=portal.portal_categories.ledger.automated.getUid(),
    grouping_reference=None
)):

  section_uid = brain.getDestinationSectionUid(portal_type=["Person", "Organisation"])
  if section_uid is not None:
    entity_uid_list.append(section_uid)

if entity_uid_list:
  portal.portal_catalog.searchAndActivate(
    portal_type=["Person", "Organisation"],
    validation_state="validated",
    uid=entity_uid_list,
    method_id='Entity_checkToCreateRegularisationRequest',
    activate_kw={'tag': tag}
  )
context.activate(after_tag=tag).getId()
