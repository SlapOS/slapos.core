requester_instance = state_change['object']
portal = requester_instance.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

context.REQUEST.set('request_instance', None)

# Required args
software_release_url_string = kwargs['software_release']
software_title = kwargs["software_title"]
software_type = kwargs["software_type"]
instance_xml = kwargs["instance_xml"]
sla_xml = kwargs["sla_xml"]
is_slave = kwargs["shared"]
root_state = kwargs["state"]

if is_slave not in [True, False]:
  raise ValueError("shared should be a boolean")

# Instance tree is used as the root of the instance tree
if requester_instance.getPortalType() == "Instance Tree":
  instance_tree = requester_instance

  # Do not propagate instante tree changes if current user
  # subscription status is not OK
  subscription_state = instance_tree.Item_getSubscriptionStatus()
  if subscription_state in ('not_subscribed', 'nopaid'):
    context.REQUEST.set('request_instance', None)
    return
  elif subscription_state in ('subscribed', 'todestroy'):
    pass
  else:
    raise NotImplementedError('Unhandled subscription state: %s' % subscription_state)

else:
  instance_tree = requester_instance.getSpecialiseValue(portal_type="Instance Tree")

# Instance can be moved from one requester to another
# Prevent creating two instances with the same title
instance_tree.serialize()
tag = "%s_%s_inProgress" % (instance_tree.getUid(), software_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0) or context.Base_getTransactionalTag(tag):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

# graph allows to "simulate" tree change after requested operation
graph = {}
successor_list = instance_tree.getSuccessorValueList()
graph[instance_tree.getUid()] = [successor.getUid() for successor in successor_list]
while True:
  try:
    current_software_instance = successor_list.pop(0)
  except IndexError:
    break
  current_software_instance_successor_list = current_software_instance.getSuccessorValueList() or []
  graph[current_software_instance.getUid()] = [successor.getUid()
                                               for successor in current_software_instance_successor_list]
  successor_list.extend(current_software_instance_successor_list)

# Check if it already exists
request_software_instance_list = portal.portal_catalog(
  # Fetch all portal type, as it is not allowed to change it
  portal_type=["Software Instance", "Slave Instance"],
  title={'query': software_title, 'key': 'ExactMatch'},
  specialise_uid=instance_tree.getUid(),
  # Do not fetch destroyed instances
  # XXX slap_state=["start_requested", "stop_requested"],
  validation_state="validated",
  limit=2,
)
instance_count = len(request_software_instance_list)
if instance_count == 0:
  request_software_instance = None
elif instance_count == 1:
  request_software_instance = request_software_instance_list[0].getObject()
else:
  raise ValueError("Too many instances '%s' found: %s" % (software_title, [x.path for x in request_software_instance_list]))

if (request_software_instance is None):
  if (root_state == "destroyed"):
    instance_found = False
  else:
    instance_found = True
    # First time that the software instance is requested
    successor = None

    # Create a new one
    reference = "SOFTINST-%s" % portal.portal_ids.generateNewId(
      id_group='slap_software_instance_reference',
      id_generator='uid')

    if is_slave == True:
      software_instance_portal_type = "Slave Instance"
    else:
      software_instance_portal_type = "Software Instance"

    module = portal.getDefaultModule(portal_type="Software Instance")
    request_software_instance = module.newContent(
      portal_type=software_instance_portal_type,
      title=software_title,
      specialise_value=instance_tree,
      follow_up_value=instance_tree.getFollowUpValue(portal_type='Project'),
      reference=reference,
      activate_kw={'tag': tag}
    )
    if software_instance_portal_type == "Software Instance":
      request_software_instance.generateCertificate()
    request_software_instance.validate()

    graph[request_software_instance.getUid()] = []

else:
  instance_found = True
  # Update the successor category of the previous requester
  successor = request_software_instance.getSuccessorRelatedValue(portal_type="Software Instance")
  if (successor is None):
    # Check if the precessor is a Instance Tree
    instance_tree_successor = request_software_instance.getSuccessorRelatedValue(portal_type="Instance Tree")
    if (requester_instance.getPortalType() != "Instance Tree" and instance_tree_successor is not None):
      raise ValueError('It is disallowed to request root software instance %s' % request_software_instance.getRelativeUrl())
    else:
      successor = requester_instance
      # It was a loose node, so check if it ok:
      if request_software_instance.getUid() not in graph:
        graph[request_software_instance.getUid()] = request_software_instance.getSuccessorUidList()

  successor_uid_list = successor.getSuccessorUidList()  
  if successor != requester_instance:
    if request_software_instance.getUid() in successor_uid_list:
      successor_uid_list.remove(request_software_instance.getUid())
      successor.edit(
        successor_uid_list=successor_uid_list,
        activate_kw={'tag': tag}
      )
  graph[successor.getUid()] = successor_uid_list

if instance_found:

  # Change desired state
  promise_kw = {
    'instance_xml': instance_xml,
    'software_type': software_type,
    'sla_xml': sla_xml,
    'software_release': software_release_url_string,
    'shared': is_slave,
  }
  request_software_instance_url = request_software_instance.getRelativeUrl()
  context.REQUEST.set('request_instance', request_software_instance)
  context.Base_setTransactionalTag(tag)
  if (root_state == "started"):
    request_software_instance.requestStart(**promise_kw)
  elif (root_state == "stopped"):
    request_software_instance.requestStop(**promise_kw)
  elif (root_state == "destroyed"):
    request_software_instance.requestDestroy(**promise_kw)
    context.REQUEST.set('request_instance', None)
  else:
    raise ValueError("state should be started, stopped or destroyed")

  successor_list = requester_instance.getSuccessorList()
  successor_uid_list = requester_instance.getSuccessorUidList()
  if successor != requester_instance:
    successor_list.append(request_software_instance_url)
    successor_uid_list.append(request_software_instance.getUid())
  uniq_successor_list = list(set(successor_list))
  successor_list.sort()
  uniq_successor_list.sort()

  assert successor_list == uniq_successor_list, "%s != %s" % (successor_list, uniq_successor_list)

  # update graph to reflect requested operation
  graph[requester_instance.getUid()] = successor_uid_list

  # check if all elements are still connected and if there is no cycle
  request_software_instance.checkConnected(graph, instance_tree.getUid())
  request_software_instance.checkNotCyclic(graph)

  if successor != requester_instance:
    requester_instance.edit(
      successor_list=successor_list,
      activate_kw={'tag': tag}
    )
else:
  context.REQUEST.set('request_instance', None)
