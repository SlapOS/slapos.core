from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

compute_partition = context
remote_node = compute_partition.getParentValue()
assert remote_node.getPortalType() == 'Remote Node'

if local_instance_list is None:
  if compute_partition.getId() == 'SHARED_REMOTE':
    # Hardcoded ID behaviour
    search_kw = dict(
      portal_type='Slave Instance',
      aggregate__uid=compute_partition.getUid(),
      validation_state='validated'
    )

  else:
    search_kw = dict(
      portal_type='Software Instance',
      aggregate__uid=compute_partition.getUid(),
      validation_state='validated'
    )
else:
  search_kw = dict(uid=[portal.restrictedTraverse(x).getUid() for x in local_instance_list])

# Partition may have a lot of Slave Instance in case of CDN.
# Create many activities, to use all activity nodes, reduce transaction time,
# and reduce conflict cost
if activate_kw is None:
  activate_kw = {}
portal.portal_catalog.searchAndActivate(
  method_id='SoftwareInstance_propagateRemoteNode',
  method_kw={"activate_kw": activate_kw},
  activate_kw=activate_kw,
  **search_kw
)
