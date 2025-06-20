from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

not_migrated_instance_tree_dict = {}

portal = context.getPortalObject()
instance_tree = context.getObject()
instance_tree_relative_url = instance_tree.getRelativeUrl()
software_instance = ([x for x in instance_tree.getSuccessorValueList() if x.getTitle()==instance_tree.getTitle()] + [None])[0]

sla_xml_dict = {}
if software_instance is not None:
  try:
    sla_xml_dict = software_instance.getSlaXmlAsDict()
  except: # pylint: disable=bare-except
    # XMLSyntaxError
    pass

last_affectation_list = instance_tree.Item_getAffectationList()
project_relative_url = None
if last_affectation_list and last_affectation_list[0].project_uid:
  project_uid = last_affectation_list[0].project_uid
  project_relative_url = portal.portal_catalog.getResultValue(uid=project_uid).getRelativeUrl()

not_migrated_instance_tree_dict[instance_tree_relative_url] = {
  'title': instance_tree.getTitle(),
  'slap_state': instance_tree.getSlapState(),
  'destination_section': instance_tree.getDestinationSection(None),
  'project_relative_url': project_relative_url,
  'allocated_instance_list': []
}
for sql_instance in portal.portal_catalog(specialise__uid=instance_tree.getUid()):
  if sql_instance.getAggregate(None) is not None:
    not_migrated_instance_tree_dict[instance_tree_relative_url]['allocated_instance_list'].append(sql_instance.getRelativeUrl())

# Node requested to be allocated on a specific project
# Use this one first, as it is currently used for payable service
# and so, it must be kept on the project with the payable trade condition
# Update: in reality, those instances are not hosted on nodes from this project
#         so drop this condition
if 0: #(software_instance is not None) and (sla_xml_dict.get('project_guid', None) is not None): # pylint: disable=using-constant-test
  project_reference = sla_xml_dict.get('project_guid', None)
  project = portal.portal_catalog.getResultValue(portal_type='Project', reference=project_reference)
  if project is not None:
    instance_tree.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
    not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# Node linked to a project
elif not_migrated_instance_tree_dict[instance_tree_relative_url]['project_relative_url'] is not None:

  instance_tree.activate().Base_activateObjectMigrationToVirtualMaster(not_migrated_instance_tree_dict[instance_tree_relative_url]['project_relative_url'])
  not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# Node requested to be allocated on a specific node
elif (software_instance is not None) and (instance_tree.getValidationState() != 'archived') and (sla_xml_dict.get('computer_guid', None) is not None):
  project_instance_reference = sla_xml_dict.get('computer_guid', None)
  project_instance = portal.portal_catalog.getResultValue(portal_type='Compute Node', reference=project_instance_reference)

  if project_instance is not None:
    project = project_instance.getFollowUpValue(None)
    if project is not None:
      instance_tree.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
      not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# Slave Node requested to be allocated on a specific project instance
elif (software_instance is not None) and (instance_tree.getValidationState() != 'archived') and (sla_xml_dict.get('instance_guid', None) is not None):
  project_instance_reference = sla_xml_dict.get('instance_guid', None)
  project_instance = portal.portal_catalog.getResultValue(portal_type='Software Instance', reference=project_instance_reference)

  if project_instance is not None:
    project = project_instance.getFollowUpValue(None)
    if project is not None:
      instance_tree.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
      not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# Finally, use the same project than the allocation
elif (software_instance is not None) and (software_instance.getAggregateValue(None) is not None):

  project = software_instance.getAggregateValue().getParentValue().getFollowUpValue(None)
  if project is not None:
    instance_tree.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
    not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# If no instance is allocated, it will probably never be. Move to personal
elif ((len(not_migrated_instance_tree_dict[instance_tree_relative_url]['allocated_instance_list']) == 0) and
      (not_migrated_instance_tree_dict[instance_tree_relative_url]['destination_section'] is not None)):

  instance_tree.getDestinationSectionValue().Person_checkSiteMigrationCreatePersonalVirtualMaster([instance_tree_relative_url])
  not_migrated_instance_tree_dict.pop(instance_tree_relative_url)

# Outdated instance tree will move to the personal project
# as, there is no way to know where it has been allocated previously
elif (not_migrated_instance_tree_dict[instance_tree_relative_url]['slap_state'] == 'destroy_requested') and \
  (not_migrated_instance_tree_dict[instance_tree_relative_url]['project_relative_url'] is None) and \
  (not_migrated_instance_tree_dict[instance_tree_relative_url]['destination_section'] is not None):

  instance_tree.getDestinationSectionValue().Person_checkSiteMigrationCreatePersonalVirtualMaster([instance_tree_relative_url])
  not_migrated_instance_tree_dict.pop(instance_tree_relative_url)
