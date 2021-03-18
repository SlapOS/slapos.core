import json
computer = context
portal = context.getPortalObject()
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if computer.getAllocationScope() not in ['open/public', 'open/subscription']:
  # Don't update non public computer
  return

can_allocate = True
comment = ''

# First and simple way to see if computer is dead
# modification_date = portal.portal_workflow.getInfoFor(computer, 'time', wf_id='edit_workflow')
# if (DateTime() - modification_date) > 1:
#   # Computer didn't talk to vifib for 1 days, do not consider it as a trustable public server for now
#   # slapformat is supposed to run at least once per day
#   can_allocate = False
#   comment = "Computer didn't contact the server for more than one day"

if can_allocate:
  # Check if computer has error reported
  memcached_dict = context.Base_getSlapToolMemcachedDict()
  try:
    d = memcached_dict[computer.getReference()]
  except KeyError:
    can_allocate = False
    comment = "Computer didn't contact the server"
  else:
    log_dict = json.loads(d)
    if '#error' in log_dict.get('text', '#error'):
      can_allocate = False
      comment = 'Computer reported an error'
    # XXX TODO: compare creation date of #ok message
    elif int(DateTime()) - int(DateTime(log_dict.get('created_at'))) > 600:
      can_allocate = False
      comment = "Computer didn't contact for more than 10 minutes"

if can_allocate:
  # Check the computer capacity.
  # there is a arbitrary hardcoded default value: not more than 1000000 (!) instances on
  # a computer.
  default_maximum_value = 1000000
  computer_capacity_quantity = computer.getCapacityQuantity(default_maximum_value)
  if computer_capacity_quantity == default_maximum_value:
    # Verify if Computer Model defines it:
    computer_model = computer.getSpecialiseValue(portal_type='Computer Model')
    if computer_model is not None:
      computer_capacity_quantity = computer_model.getCapacityQuantity(default_maximum_value)

    # The update the computer with the initial value.
    if computer_capacity_quantity != default_maximum_value:
      computer.edit(capacity_quantity=computer_capacity_quantity)

  software_release_capacity_dict = {}
  consumed_capacity = 0

  def getSoftwareReleaseCapacity(instance):
    software_release_url = instance.getUrlString()
    software_type = instance.getSourceReference()
    if "%s-%s" % (software_release_url, software_type) in software_release_capacity_dict:
      return software_release_capacity_dict["%s-%s" % (software_release_url, software_type)]

    software_release = portal.portal_catalog.getResultValue(
      portal_type='Software Release',
      url_string={'query': software_release_url, 'key': 'ExactMatch'})

    software_release_capacity = None
    if software_release is not None:
      # Search for Software Product Individual Variation with same reference
      software_product = software_release.getAggregateValue()
      if software_product is not None:
        for variation in software_product.searchFolder(
            portal_type="Software Product Individual Variation",
            reference=software_type):
          software_release_capacity = variation.getCapacityQuantity(None)
          if software_release_capacity is not None:
            break

        if software_release_capacity is None:
          software_release_capacity = software_product.getCapacityQuantity(None)

      if software_release_capacity is None:
        software_release_capacity = software_release.getCapacityQuantity(1)

    if software_release_capacity is None:
      software_release_capacity = 1

    software_release_capacity_dict["%s-%s" % (software_release_url, software_type)] = software_release_capacity
    return software_release_capacity

  if allocated_instance is not None:
    software_release_capacity = getSoftwareReleaseCapacity(allocated_instance)
    consumed_capacity += software_release_capacity
    if consumed_capacity >= computer_capacity_quantity:
      can_allocate = False
      comment = 'Computer capacity limit exceeded (%s >= %s)' % (consumed_capacity, computer_capacity_quantity)

  if can_allocate:
    for instance in portal.portal_catalog.portal_catalog(
        default_aggregate_relative_url='%s/%%' % computer.getRelativeUrl(),
        portal_type=['Software Instance', 'Slave Instance'],
        validation_state='validated'):

      software_release_capacity = getSoftwareReleaseCapacity(instance.getObject())
      consumed_capacity += software_release_capacity
      if consumed_capacity >= computer_capacity_quantity:
        can_allocate = False
        comment = 'Computer capacity limit exceeded'
        break

# if can_allocate:
#   result_list = portal.portal_catalog.portal_catalog(
#     parent_uid=computer.getUid(),
#     portal_type='Computer Partition',
#     free_for_request=1,
#     limit=1)
#   if len(result_list) == 0:
#     can_allocate = False
#     comment = 'No free partition left'

new_value = None
if can_allocate:
  if computer.getCapacityScope() == 'close':
    new_value = 'open'
else:
  if computer.getCapacityScope() == 'open':
    new_value = 'close'

if new_value is not None:
  computer.edit(capacity_scope=new_value)
  if comment:
    portal.portal_workflow.doActionFor(computer, 'edit_action', comment=comment)
