from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance = context
portal = context.getPortalObject()

if instance.getValidationState() != 'validated' \
  or instance.getSlapState() not in ('start_requested', 'stop_requested') \
  or instance.getAggregateValue(portal_type='Computer Partition') is not None:
  return

latest_comment = portal.portal_workflow.getInfoFor(instance, 'comment', wf_id='edit_workflow')
if latest_comment not in ('Allocation failed: no free Computer Partition', 'Allocation failed: Allocation disallowed'):
  # No nothing if allocation alarm didn't run on it
  return

latest_edit_time = portal.portal_workflow.getInfoFor(instance, 'time', wf_id='edit_workflow')
if (int(DateTime()) - int(latest_edit_time)) < 259200:
  # Allow 3 days gap betweeb latest allocation try and deletion
  return

# Only destroy if the instance is the only one in the tree
instance_tree = instance.getSpecialiseValue("Instance Tree")
if (instance_tree.getSuccessor() != instance.getRelativeUrl()):
  return
if (len(instance_tree.getSuccessorList()) != 1):
  return
instance_list = portal.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  default_specialise_uid=instance_tree.getUid(),
  limit=2)
if len(instance_list) != 1:
  return

# OK, destroy instance tree
instance_tree.requestDestroy(
  software_release=instance_tree.getUrlString(),
  software_title=instance_tree.getTitle(),
  software_type=instance_tree.getSourceReference(),
  instance_xml=instance_tree.getTextContent(),
  sla_xml=instance_tree.getSlaXml(),
  shared=instance_tree.isRootSlave(),
  state='destroyed',
  comment="Garbage collect %s not allocated for more than 3 days" % instance.getRelativeUrl(),
)
instance_tree.archive()
