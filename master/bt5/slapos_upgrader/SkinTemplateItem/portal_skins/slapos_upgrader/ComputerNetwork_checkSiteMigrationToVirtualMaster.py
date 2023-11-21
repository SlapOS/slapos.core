from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
computer_network = context.getObject()
computer_network_relative_url = computer_network.getRelativeUrl()

last_affectation_list = computer_network.Item_getAffectationList()
project_relative_url = None
if last_affectation_list and last_affectation_list[0].project_uid:
  project_uid = last_affectation_list[0].project_uid
  project_relative_url = portal.portal_catalog.getResultValue(uid=project_uid).getRelativeUrl()

not_migrated_computer_network = {
  'title': computer_network.getTitle(),
  'project_relative_url': project_relative_url,
  # Category has been dropped from the Computer Network portal type
  'source_administration': ([x[len('source_administration/'):] for x in computer_network.getCategoryList() if x.startswith('source_administration')] or [None])[0],
}

# If network has no compute node, move it to user personal project
compute_node_list = [x.getObject() for x in portal.portal_catalog(
  portal_type="Compute Node",
  subordination__uid=computer_network.getUid()
)]
project_list = [x.getFollowUp(None) for x in compute_node_list]
project_list = list(set(project_list))

# Node linked to a project
if not_migrated_computer_network['project_relative_url'] is not None:
  computer_network.activate().Base_activateObjectMigrationToVirtualMaster(not_migrated_computer_network['project_relative_url'])

elif (len(compute_node_list) == 0) and (not_migrated_computer_network['source_administration'] is not None):
  # No compute node. Move it to user personal project
  source_administration_value = portal.restrictedTraverse(not_migrated_computer_network['source_administration'])
  source_administration_value.Person_checkSiteMigrationCreatePersonalVirtualMaster([computer_network_relative_url])

elif (len(project_list) == 1) and (project_list[0] is not None):
  # All nodes are linked to the same project
  computer_network.activate().Base_activateObjectMigrationToVirtualMaster(project_list[0])
