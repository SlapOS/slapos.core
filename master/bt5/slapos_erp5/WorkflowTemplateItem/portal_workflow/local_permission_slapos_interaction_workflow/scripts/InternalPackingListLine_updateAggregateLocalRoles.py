portal_type_list = ['Computer', 'Computer Network', 'Hosting Subscription']
internal_packing_list_line = state_change['object']
after_tag = (internal_packing_list_line.getPath(), ('immediateReindexObject', 'recursiveImmediateReindexObject'))
internal_packing_list_line.getParentValue().reindexObject()
for object_ in internal_packing_list_line.getAggregateValueList(portal_type=portal_type_list):
  object_.activate(after_path_and_method_id=after_tag).updateLocalRolesOnSecurityGroups()
  if object_.getPortalType() == "Computer":
    for software_installation in object_.getAggregateRelatedValueList(portal_type="Software Installation"):
      software_installation.activate(after_path_and_method_id=after_tag).updateLocalRolesOnSecurityGroups()
    
  elif object_.getPortalType() == "Hosting Subscription":
    for instance in object_.getSpecialiseRelatedValueList(portal_type=["Software instance", "Slave Instance"]):
      instance.activate(after_path_and_method_id=after_tag).updateLocalRolesOnSecurityGroups()
