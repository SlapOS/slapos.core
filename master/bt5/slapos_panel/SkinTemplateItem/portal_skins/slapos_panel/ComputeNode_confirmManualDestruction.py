from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

compute_node = context
compute_node_relative_url = compute_node.getRelativeUrl()
portal = context.getPortalObject()

if (compute_node.getAllocationScope() != 'close/forever') or \
  (compute_node.getValidationState() != 'validated') or \
  (compute_node.getLastAccessDate() != "Compute Node didn't contact the server"):
  return compute_node.Base_redirect(
    'view',
    keep_items={
      'portal_status_level': 'warning',
      'portal_status_message': compute_node.Base_translateString("You're not allowed to manually confirm the destruction.")
    }
  )

for sql_result in portal.portal_catalog(
  portal_type=['Software Instance', 'Slave Instance'],
  validation_state='validated',
  aggregate__parent_uid=compute_node.getUid()
):
  instance = sql_result.getObject()
  if instance.getValidationState() != 'validated':
    continue
  partition = instance.getAggregateValue(portal_type='Compute Partition')
  if partition is None:
    continue
  assert partition.getParentValue().getRelativeUrl() == compute_node_relative_url, partition.getRelativeUrl()
  assert partition.getSlapState() == 'busy', partition.getRelativeUrl()

  # request destruction of the instance if it is not
  if instance.getSlapState() != 'destroy_requested':
    instance.SoftwareInstance_renameAndRequestDestroy()
  assert instance.getSlapState() == 'destroy_requested', instance.getSlapState()
  # Manually confirm the instance destruction
  if instance.getPortalType() == 'Software Instance':
    # XXX Move this code to aanother bt5
    # remove certificate from SI
    instance.revokeCertificate()
    instance.invalidate()
    instance.setAccessStatus('Instance manually destroyed', "destroyed", reindex=1)

  # Unallocation will be done by an alarm
# Compute Node invalidation will be done by an alarm

return compute_node.Base_redirect('view', keep_items={'portal_status_message': compute_node.Base_translateString('Destruction Confirmed.')})
