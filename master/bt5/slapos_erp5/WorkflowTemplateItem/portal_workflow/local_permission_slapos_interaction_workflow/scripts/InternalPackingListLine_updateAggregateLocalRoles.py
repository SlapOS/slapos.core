from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

portal_type_list = ['Computer', 'Computer Network', 'Instance Tree']
portal = context.getPortalObject()
internal_packing_list_line = state_change['object']
after_tag = (internal_packing_list_line.getPath(), ('immediateReindexObject', 'recursiveImmediateReindexObject'))
internal_packing_list_line.getParentValue().reindexObject()
for object_ in internal_packing_list_line.getAggregateValueList(portal_type=portal_type_list):
  object_.activate(after_path_and_method_id=after_tag).updateLocalRolesOnSecurityGroups()
  if object_.getPortalType() == "Computer":
    portal.portal_catalog.searchAndActivate(
      portal_type=["Software Installation", "Support Request","Upgrade Decision"],
      default_or_child_aggregate_uid=object_.getUid(),
      method_id="Base_updateSlapOSLocalRolesOnSecurityGroups",
      method_kw=dict(activate_kw={"after_path_and_method_id": after_tag}),
      activate_kw={"after_path_and_method_id": after_tag}
    )
    
  elif object_.getPortalType() == "Instance Tree":
    query = ComplexQuery(
      ComplexQuery(
        SimpleQuery(portal_type=["Software instance", "Slave Instance"]),
        SimpleQuery(default_specialise_uid=object_.getUid()),
        logical_operator="AND"),
      ComplexQuery(
        SimpleQuery(portal_type=["Support Request", "Upgrade Decision"]),
        SimpleQuery(default_or_child_aggregate_uid=object_.getUid()),
        logical_operator="AND"),
      logical_operator="OR"
    )
    portal.portal_catalog.searchAndActivate(
      query=query,
      method_id="Base_updateSlapOSLocalRolesOnSecurityGroups",
      method_kw=dict(activate_kw={"after_path_and_method_id": after_tag}),
      activate_kw={"after_path_and_method_id": after_tag}
    )
