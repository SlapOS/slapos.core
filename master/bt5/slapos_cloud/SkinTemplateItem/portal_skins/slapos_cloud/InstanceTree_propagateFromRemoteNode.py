from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance_tree = context
portal = context.getPortalObject()
title = instance_tree.getTitle()

# parse the title, to find which Instance leads to the Instance Tree creation
# '_remote_%s_%s' % (remote_node.getFollowUpReference(), local_instance.getReference())

empty, prefix, project_reference, instance_reference = title.split('_', 3)
assert empty == ''
assert prefix == 'remote'

if instance_reference is not None:
  instance_list = portal.portal_catalog(
    portal_type=['Slave Instance', 'Software Instance'],
    reference=instance_reference,
    follow_up__reference=project_reference,
    validation_state='validated',
    limit=2
  )
  if len(instance_list) == 1:
    instance = instance_list[0]
    instance.SoftwareInstance_propagateRemoteNode(activate_kw=activate_kw)
