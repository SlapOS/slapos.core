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
except KeyError:
  raise TypeError("Person_requestSoftwareInstance takes exactly 7 arguments")

if is_slave not in [True, False]:
  raise ValueError("shared should be a boolean")

instance_tree_portal_type = "Instance Tree"

tag = "%s_%s_inProgress" % (person.getUid(),
                               software_title)

if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

# Check if it already exists
request_instance_tree_list = portal.portal_catalog(
  portal_type=instance_tree_portal_type,
  title={'query': software_title, 'key': 'ExactMatch'},
  validation_state="validated",
  default_destination_section_uid=person.getUid(),
  limit=2,
  )
if len(request_instance_tree_list) > 1:
  raise NotImplementedError("Too many instance tree %s found %s" % (software_title, [x.path for x in request_instance_tree_list]))
elif len(request_instance_tree_list) == 1:
  request_instance_tree = request_instance_tree_list[0].getObject()
  if (request_instance_tree.getSlapState() == "destroy_requested") or \
     (request_instance_tree.getTitle() != software_title) or \
     (request_instance_tree.getValidationState() != "validated") or \
     (request_instance_tree.getDestinationSection() != person.getRelativeUrl()):
    raise NotImplementedError("The system was not able to get the expected instance tree")
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
    upgrade_scope="auto",
    activate_kw={'tag': tag},
  )

promise_kw = {
  'instance_xml': instance_xml,
  'software_type': software_type,
  'sla_xml': sla_xml,
  'software_release': software_release_url_string,
  'shared': is_slave,
}

context.REQUEST.set('request_instance_tree', request_instance_tree)
# Change desired state
if (root_state == "started"):
  request_instance_tree.requestStart(**promise_kw)
elif (root_state == "stopped"):
  request_instance_tree.requestStop(**promise_kw)
elif (root_state == "destroyed"):
  request_instance_tree.requestDestroy(**promise_kw)
  context.REQUEST.set('request_instance_tree', None)
else:
  raise ValueError("state should be started, stopped or destroyed")

request_instance_tree.requestInstance(
  software_release=software_release_url_string,
  software_title=software_title,
  software_type=software_type,
  instance_xml=instance_xml,
  sla_xml=sla_xml,
  shared=is_slave,
  state=root_state,
)

# Change the state at the end to allow to execute updateLocalRoles only once in the transaction
validation_state = request_instance_tree.getValidationState()
slap_state = request_instance_tree.getSlapState()
if validation_state == 'draft':
  request_instance_tree.portal_workflow.doActionFor(request_instance_tree,
                                           'validate_action')
if (validation_state != 'archived') and \
   (slap_state == 'destroy_requested'):
  # XXX TODO do not use validation workflow to filter destroyed subscription
  request_instance_tree.archive()
