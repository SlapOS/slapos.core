person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  compute_node_title = kwargs['compute_node_title']
except KeyError:
  raise TypeError("Person_requestComputeNode takes exactly 2 arguments. Missing compute_node_title.")

try:
  project_reference = kwargs['project_reference']
except KeyError:
  raise TypeError("Person_requestComputeNode takes exactly 2 arguments. Missing project_reference.")

tag = "%s_%s_ComputeNodeInProgress" % (person.getUid(), 
                               compute_node_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

# Ensure project is correctly set
project_list = portal.portal_catalog.portal_catalog(portal_type='Project', reference=project_reference,
                                                    validation_state='validated', limit=2)
if len(project_list) != 1:
  raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))

compute_node_portal_type = "Compute Node"
compute_node_list = portal.portal_catalog.portal_catalog(
  portal_type=compute_node_portal_type,
  title={'query': compute_node_title, 'key': 'ExactMatch'},
  validation_state='validated',
  follow_up__uid=project_list[0].getUid(),
  limit=2
)

if len(compute_node_list) == 2:
  raise NotImplementedError
elif len(compute_node_list) == 1:
  compute_node = compute_node_list[0]
  assert compute_node.getFollowUp() == project_list[0].getRelativeUrl()
else:

  reference = "COMP-%s" % portal.portal_ids.generateNewId(
    id_group='slap_computer_reference',
    id_generator='uid')
  module = portal.getDefaultModule(portal_type=compute_node_portal_type)
  compute_node = module.newContent(
    portal_type=compute_node_portal_type,
    title=compute_node_title,
    reference=reference,
    follow_up_value=project_list[0],
    activate_kw={'tag': tag}
  )
  compute_node.approveComputeNodeRegistration()


compute_node = context.restrictedTraverse(compute_node.getRelativeUrl())

context.REQUEST.set("compute_node", compute_node.getRelativeUrl())
context.REQUEST.set("compute_node_url", compute_node.absolute_url())
context.REQUEST.set("compute_node_reference", compute_node.getReference())
