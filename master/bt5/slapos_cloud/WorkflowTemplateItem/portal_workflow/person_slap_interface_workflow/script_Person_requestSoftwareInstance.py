person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  software_release_url_string = kwargs['software_release']
  software_title = kwargs["software_title"]
  software_type = kwargs["software_type"]
  instance_xml = kwargs["instance_xml"]
  sla_xml = kwargs["sla_xml"]
  is_slave = kwargs["shared"]
  root_state = kwargs["state"]
  project_reference = kwargs['project_reference']
except KeyError:
  raise TypeError("Person_requestSoftwareInstance takes exactly 8 arguments")

if is_slave not in [True, False]:
  raise ValueError("shared should be a boolean")

instance_tree_portal_type = "Instance Tree"

tag = "%s_%s_inProgress" % (person.getUid(),
                               software_title)

if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

# Ensure project is correctly set
assert project_reference, 'No project reference'
project_list = portal.portal_catalog.portal_catalog(portal_type='Project', reference=project_reference,
                                                    validation_state='validated', limit=2)
if len(project_list) != 1:
  raise NotImplementedError("%i projects '%s'" % (len(project_list), project_reference))

# Check if it already exists
request_instance_tree_list = portal.portal_catalog(
  portal_type=instance_tree_portal_type,
  title={'query': software_title, 'key': 'ExactMatch'},
  validation_state="validated",
  destination_section__uid=person.getUid(),
  limit=2,
  )
if len(request_instance_tree_list) > 1:
  raise NotImplementedError("Too many instance tree %s found %s" % (software_title, [x.path for x in request_instance_tree_list]))
elif len(request_instance_tree_list) == 1:
  request_instance_tree = request_instance_tree_list[0].getObject()
  assert request_instance_tree.getFollowUp() == project_list[0].getRelativeUrl()
  if (request_instance_tree.getSlapState() == "destroy_requested") or \
     (request_instance_tree.getTitle() != software_title) or \
     (request_instance_tree.getValidationState() != "validated") or \
     (request_instance_tree.getDestinationSection() != person.getRelativeUrl()):
    raise NotImplementedError("The system was not able to get the expected instance tree")
  # Do not allow user to change the release/type/shared status
  # This is not compatible with invoicing the service
  # Instance release change will be handled by allocation supply and upgrade decision
  if ((request_instance_tree.getUrlString() != software_release_url_string) or \
      (request_instance_tree.getSourceReference() != software_type) or \
      (request_instance_tree.getRootSlave() != is_slave)) and \
     (not kwargs.get("force_software_change", False)):
    raise NotImplementedError("You can not change the release / type / shared states")
else:
  if (root_state == "destroyed"):
    # No need to create destroyed subscription.
    context.REQUEST.set('request_instance_tree', None)
    return
  instance_tree_reference = "HOSTSUBS-%s" % context.getPortalObject().portal_ids\
      .generateNewId(id_group='slap_hosting_subscription_reference', id_generator='uid')
  request_instance_tree = portal.getDefaultModule(portal_type=instance_tree_portal_type).newContent(
    portal_type=instance_tree_portal_type,
    reference=instance_tree_reference,
    title=software_title,
    destination_section=person.getRelativeUrl(),
    follow_up_value=project_list[0],
    activate_kw={'tag': tag},
  )

request_instance_tree.InstanceTree_updateParameterAndRequest(
  root_state, software_release_url_string, software_title, software_type, instance_xml, sla_xml, is_slave
)
context.REQUEST.set('request_instance_tree', request_instance_tree)
if (root_state == "destroyed"):
  context.REQUEST.set('request_instance_tree', None)
