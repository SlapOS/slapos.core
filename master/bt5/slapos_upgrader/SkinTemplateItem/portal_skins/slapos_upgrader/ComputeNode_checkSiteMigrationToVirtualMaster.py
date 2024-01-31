from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

not_migrated_compute_node_dict = {}

portal = context.getPortalObject()
compute_node = context.getObject()
compute_node_relative_url = compute_node.getRelativeUrl()

last_affectation_list = compute_node.Item_getAffectationList()
project_relative_url = None
if last_affectation_list and last_affectation_list[0].project_uid:
  project_uid = last_affectation_list[0].project_uid
  project_relative_url = portal.portal_catalog.getResultValue(uid=project_uid).getRelativeUrl()

not_migrated_compute_node = {
  'title': compute_node.getTitle(),
  'allocation_scope': compute_node.getAllocationScope(""),
  'project_relative_url': project_relative_url,
  # Category has been dropped from the Compute Node portal type
  'source_administration': ([x[len('source_administration/'):] for x in compute_node.getCategoryList() if x.startswith('source_administration')] or [None])[0],
  'instance_list': []
}
source_administration_value = portal.restrictedTraverse(not_migrated_compute_node['source_administration'])

not_migrated_compute_node_dict[compute_node_relative_url] = not_migrated_compute_node

partition_list = compute_node.contentValues(portal_type='Compute Partition')
instance_tree_list = []

for partition in partition_list:
  instance_list = portal.portal_catalog(
    portal_type=['Slave Instance', 'Software Instance'],
    aggregate__uid=partition.getUid()
  )
  not_migrated_compute_node['instance_list'].extend([x.getRelativeUrl() for x in instance_list])

  for instance in instance_list:
    instance_tree_list.append(instance.getSpecialiseValue())
    # XXX check if the instance tree is only hosted on this machine

instance_tree_list = list(set(instance_tree_list))
computer_network = compute_node.getSubordinationValue(portal_type="Computer Network")

# Already migrate unused compute node
if (len(not_migrated_compute_node['instance_list']) == 0) and \
  (not_migrated_compute_node['project_relative_url'] is None) and \
  ((not not_migrated_compute_node['allocation_scope'].startswith('open')) or (not_migrated_compute_node['allocation_scope'] == 'open/personal')):

  not_migrated_compute_node_dict.pop(compute_node_relative_url)
  source_administration_value.Person_checkSiteMigrationCreatePersonalVirtualMaster([compute_node_relative_url])

# Node linked to a project
elif not_migrated_compute_node['project_relative_url'] is not None:

  compute_node.activate().Base_activateObjectMigrationToVirtualMaster(not_migrated_compute_node['project_relative_url'])
  not_migrated_compute_node_dict.pop(compute_node_relative_url)

elif (computer_network is not None) and (computer_network.getFollowUp(None) is not None):
  # Network is already linked to a project
  compute_node.activate().Base_activateObjectMigrationToVirtualMaster(computer_network.getFollowUp())
  not_migrated_compute_node_dict.pop(compute_node_relative_url)

else:
  # If the related instance are all grouped on this machine, and from the same user
  from_same_user_only = True
  on_this_node_only = True
  instance_project_list = []
  for instance_tree in instance_tree_list:
    instance_project_list.append(instance_tree.getFollowUp(None))
    if instance_tree.getDestinationSection() != not_migrated_compute_node['source_administration']:
      from_same_user_only = False

    for software_instance in instance_tree.getSpecialiseRelatedValueList():
      partition = software_instance.getAggregate(None)
      if (partition is not None) and (partition.startswith(compute_node_relative_url)):
        on_this_node_only = False

  instance_project_list = list(set(instance_project_list))

  if from_same_user_only and on_this_node_only:
    not_migrated_compute_node_dict.pop(compute_node_relative_url)
    source_administration_value.Person_checkSiteMigrationCreatePersonalVirtualMaster([compute_node_relative_url] + [x.getRelativeUrl() for x in instance_tree_list])

  elif (len(instance_project_list) == 1) and (instance_project_list[0] is not None):
    # Else, check if all related instances tree are on the same virtual master
    not_migrated_compute_node_dict.pop(compute_node_relative_url)
    compute_node.activate().Base_activateObjectMigrationToVirtualMaster(instance_project_list[0])

  elif force_migration and (not_migrated_compute_node['source_administration'] is not None):
    if from_same_user_only:
      not_migrated_compute_node_dict.pop(compute_node_relative_url)
      source_administration_value.Person_checkSiteMigrationCreatePersonalVirtualMaster([compute_node_relative_url])
    else:
      # Create a single project for every single remaining compute node
      project = source_administration_value.Person_addVirtualMaster(
        title='Migrated shared for %s' % compute_node.getReference(),
        is_compute_node_payable=False,
        is_instance_tree_payable=False,
        # Hardcoded
        price_currency='currency_module/EUR',
        batch=1
      )
      compute_node.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
      not_migrated_compute_node_dict.pop(compute_node_relative_url)

# Log
if not_migrated_compute_node_dict:
  context.log(not_migrated_compute_node_dict.keys())
