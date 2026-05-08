portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

assert context.getPortalType() in ['Workgroup', 'Person']

# Search for the matching item
sql_node_list = portal.portal_catalog(
  reference=reference,
  # Project are not handled yet, as it must also move all compute node subscription at the same time
  portal_type='Remote Node',
  validation_state='validated',
  limit=2
)
if len(sql_node_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_node_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

subscription_change_request_list = []
remote_node = sql_node_list[0].getObject()

remote_project = remote_node.getDestinationProjectValue(portal_type='Project')
# XXX Ensure that user is customer on destination project, else no claim should be done.

remote_entity = remote_node.getDestinationSectionValue(portal_type=['Person', 'Workgroup'])

search_kw = dict(
  portal_type=['Slave Instance', 'Software Instance'],
  aggregate__uid=[p.uid for p in remote_node.contentValues(portal_type='Compute Partition')],
  validation_state='validated'
)

for local_instance in portal.portal_catalog(**search_kw):
  remote_instance_tree_list = portal.portal_catalog(
    portal_type='Instance Tree',
    validation_state='validated',
    destination_section__uid=remote_entity.getUid(),
    follow_up__uid=remote_project.getUid(),
    title={'query': '_remote_%s_%s' % (local_instance.getFollowUpReference(),
                                     local_instance.getReference()),
           'key': 'ExactMatch'},
    limit=2)
  assert len(remote_instance_tree_list) == 1, "Invalid amount of Instance Tree"
  remote_instance_tree_reference = remote_instance_tree_list[0].reference
  subscription_change_request_list.append(
    context.Person_claimSlaposItemSubscription(
      reference=remote_instance_tree_reference,
      activate_kw=activate_kw)
  )

remote_node.setDestinationSectionValue(context)
if batch:
  return subscription_change_request_list

if len(subscription_change_request_list) == 0:
  keep_items = {
    'portal_status_message': Base_translateString('Remote Node claimed.')
  }
  return remote_node.Base_redirect(keep_items=keep_items)

if len(subscription_change_request_list) == 1:
  keep_items = {
    'portal_status_message': Base_translateString('Remote Node claimed and Subscription Change created.')
  }
  return subscription_change_request_list[0].Base_redirect(keep_items=keep_items)

keep_items = {
  'portal_status_message': Base_translateString('Remote Node claimed and Several Subscription Change Request created.')
}
return context.Base_redirect(keep_items=keep_items)
