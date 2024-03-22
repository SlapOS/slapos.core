from Products.DCWorkflow.DCWorkflow import ValidationFailed
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
from zExceptions import Unauthorized

if context.getPortalType() not in ('Software Instance', 'Slave Instance'):
  raise TypeError('%s is not supported' % context.getPortalType())

def markHistory(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(ob=document,
                                          name='comment', wf_id='edit_workflow')
  if last_workflow_item != comment:
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

def assignComputePartition(software_instance, instance_tree):
  compute_partition = software_instance.getAggregateValue(
      portal_type="Compute Partition")
  if compute_partition is None:
    instance_tree = software_instance.getSpecialiseValue(
        portal_type='Instance Tree')

    if instance_tree is None:
      raise ValueError('%s does not have related instance tree' % software_instance.getRelativeUrl())

    person = instance_tree.getDestinationSectionValue(portal_type='Person')
    if person is None:
      raise ValueError('%s does not have person related' % instance_tree.getRelativeUrl())
    if not person.Person_isAllowedToAllocate():
      raise Unauthorized('Allocation disallowed')

    subscription_reference = None
    subscription_request = instance_tree.getAggregateRelatedValue(
        portal_type="Subscription Request")
    if subscription_request is not None:
      subscription_reference = subscription_request.getReference()
      if subscription_request.getSimulationState() not in ["ordered", "confirmed", "started"]:
        raise Unauthorized("Related Subscription Requested isn't ordered, confirmed or started")

    tag = None
    try:
      sla_dict = software_instance.getSlaXmlAsDict()
    except Exception:
      # Note: it is impossible to import module exceptions from python scripts
      compute_partition_relative_url = None
    else:

      # "Each instance should be allocated to a different network." (i.e at most one instance of the tree per network)
      computer_network_query = None
      if sla_dict.get('mode', None) == 'unique_by_network':
        # Prevent creating two instances in the same computer_network
        instance_tree_uid = instance_tree.getUid()
        tag = "%s_inProgress" % instance_tree_uid
        if (context.getPortalObject().portal_activities.countMessageWithTag(tag) > 0):
          # The software instance is already under creation but can not be fetched from catalog
          # As it is not possible to fetch informations, just ignore
          markHistory(software_instance,
              'Allocation failed: blocking activites in progress for %s' % instance_tree_uid)

        sla_dict.pop('mode')
        # XXX: does NOT scale if instance tree contains many SoftwareInstance
        instance_tree = software_instance.getSpecialiseValue()
        software_instance_tree_list = [sql_obj.getObject() \
            for sql_obj in context.getPortalObject().portal_catalog(
                portal_type=['Software Instance', 'Slave Instance'],
                default_specialise_uid=instance_tree.getUid(),
            )
        ]
        computer_network_query_list = []
        # Don't deploy in compute_node with no network
        computer_network_query_list.append(ComplexQuery(
            SimpleQuery(
            default_subordination_uid=''),
            logical_operator='not',
        ))
        for other_software_instance in software_instance_tree_list:
          compute_partition = other_software_instance.getAggregateValue()
          if not compute_partition:
            continue
          computer_network = compute_partition.getParentValue().getSubordinationValue()
          if computer_network:
            computer_network_query_list.append(ComplexQuery(
                SimpleQuery(
                default_subordination_uid=computer_network.getUid()),
                logical_operator='not',
            ))

        computer_network_query = ComplexQuery(*computer_network_query_list)
        instance_tree.serialize()

      elif sla_dict.get('mode'):
        computer_network_query = '-1'

      compute_partition_relative_url = person.Person_restrictMethodAsShadowUser(
        shadow_document=person,
        callable_object=person.Person_findPartition,
        argument_list=[software_instance.getUrlString(), software_instance.getSourceReference(),
        software_instance.getPortalType(), sla_dict, computer_network_query,
        subscription_reference, instance_tree.isRootSlave()])
    return compute_partition_relative_url, tag

software_instance = context
if software_instance.getValidationState() != 'validated' \
  or software_instance.getSlapState() not in ('start_requested', 'stop_requested') \
  or software_instance.getAggregateValue(portal_type='Compute Partition') is not None:
  return 

instance_tree = software_instance.getSpecialiseValue()
try:
  compute_partition_url, tag = assignComputePartition(software_instance,
      instance_tree)

  # XXX: We create a dummy activity to prevent to allocations on the same network
  if tag:
    instance_tree.activate(activity="SQLQueue", tag=tag,
        after_tag="allocate_%s" % compute_partition_url).getId()

except ValueError as e:
  # It was not possible to find free Compute Partition
  markHistory(software_instance, 'Allocation failed: no free Compute Partition %s' % e)
except Unauthorized as e:
  # user has bad balance
  markHistory(software_instance, 'Allocation failed: %s' % e)
except NotImplementedError as e:
  # user has bad balance
  markHistory(software_instance, 'Allocation failed: %s' % e)
else:
  if compute_partition_url is not None:
    try:
      software_instance.Base_checkConsistency()
    except ValidationFailed:
      # order not ready yet
      markHistory(software_instance, 'Allocation failed: consistency failed')
    else:
      software_instance.allocatePartition(compute_partition_url=compute_partition_url)
