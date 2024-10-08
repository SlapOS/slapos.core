compute_node = context
portal = context.getPortalObject()
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if compute_node.getAllocationScope() != 'open':
  # Don't update non public compute_node
  return

can_allocate = True
comment = ''

# First and simple way to see if compute_node is dead
# modification_date = portal.portal_workflow.getInfoFor(compute_node, 'time', wf_id='edit_workflow')
# if (DateTime() - modification_date) > 1:
#   # Compute Node didn't talk to vifib for 1 days, do not consider it as a trustable public server for now
#   # slapformat is supposed to run at least once per day
#   can_allocate = False
#   comment = "Compute Node didn't contact the server for more than one day"

if can_allocate:
  # Check if compute_node has error reported
  log_dict = compute_node.getAccessStatus()
  if log_dict.get("no_data") == 1:
    can_allocate = False
    comment = "Compute Node didn't contact the server"
  else:
    if '#error' in log_dict.get('text', '#error'):
      can_allocate = False
      comment = 'Compute Node reported an error'
    # XXX TODO: compare creation date of #ok message
    elif int(DateTime()) - int(DateTime(log_dict.get('created_at'))) > 600:
      can_allocate = False
      comment = "Compute Node didn't contact for more than 10 minutes"

if can_allocate:
  # Check the compute_node capacity.
  # there is a arbitrary hardcoded default value: not more than 1000000 (!) instances on
  # a compute_node.
  default_maximum_value = 1000000
  compute_node_capacity_quantity = compute_node.getCapacityQuantity(default_maximum_value)
  if compute_node_capacity_quantity == default_maximum_value:
    # Verify if Computer Model defines it:
    computer_model = compute_node.getSpecialiseValue(portal_type='Computer Model')
    if computer_model is not None:
      compute_node_capacity_quantity = computer_model.getCapacityQuantity(default_maximum_value)

    # The update the compute_node with the initial value.
    if compute_node_capacity_quantity != default_maximum_value:
      compute_node.edit(capacity_quantity=compute_node_capacity_quantity)

  consumed_capacity = 0

  def getSoftwareReleaseCapacity(instance):
    _, _, type_variation = instance.InstanceTree_getSoftwareProduct()
    if type_variation is None:
      return 1
    return type_variation.getCapacityQuantity(1)

  if allocated_instance is not None:
    consumed_capacity += getSoftwareReleaseCapacity(allocated_instance)
    if consumed_capacity >= compute_node_capacity_quantity:
      can_allocate = False
      comment = 'Compute Node capacity limit exceeded (%s >= %s)' % (consumed_capacity, compute_node_capacity_quantity)

  if can_allocate:
    for sql_instance in portal.portal_catalog.portal_catalog(
        default_aggregate_relative_url='%s/%%' % compute_node.getRelativeUrl(),
        portal_type=['Software Instance', 'Slave Instance'],
        validation_state='validated',
        group_by=['url_string', 'source_reference'],
        select_list=['COUNT(*)', 'url_string', 'source_reference']
    ):

      assert sql_instance.url_string == sql_instance.getUrlString()
      assert sql_instance.source_reference == sql_instance.getSourceReference()
      assert 1 <= sql_instance['COUNT(*)']
      consumed_capacity += getSoftwareReleaseCapacity(sql_instance) * sql_instance['COUNT(*)']
      if consumed_capacity >= compute_node_capacity_quantity:
        can_allocate = False
        comment = 'Compute Node capacity limit exceeded'
        break

# if can_allocate:
#   result_list = portal.portal_catalog.portal_catalog(
#     parent_uid=compute_node.getUid(),
#     portal_type='Compute Partition',
#     free_for_request=1,
#     limit=1)
#   if len(result_list) == 0:
#     can_allocate = False
#     comment = 'No free partition left'

new_value = None
if can_allocate:
  if compute_node.getCapacityScope() == 'close':
    new_value = 'open'
else:
  if compute_node.getCapacityScope() == 'open':
    new_value = 'close'

if new_value is not None:
  compute_node.edit(capacity_scope=new_value)
  if comment:
    portal.portal_workflow.doActionFor(compute_node, 'edit_action', comment=comment)
