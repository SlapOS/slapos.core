from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance_tree = context
portal = instance_tree.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
actor = instance_tree.getDestinationSectionValue()
Base_translateString = portal.Base_translateString

redirect_error_kw = {
  'abort_transaction': True,
  'keep_items': {
    'portal_status_level': 'error',
  }
}

request_kw = dict(
  software_release=instance_tree.getUrlString(),
  software_title=instance_tree.getTitle(),
  software_type=instance_tree.getSourceReference(),
  instance_xml=instance_tree.getTextContent(),
  sla_xml=instance_tree.getSlaXml(),
  shared=instance_tree.isRootSlave(),
  state={'start_requested': 'started',
         'destroy_requested': 'destroyed',
         'stop_requested': 'stopped'}[instance_tree.getSlapState()],
  project_reference=instance_tree.getFollowUpValue().getReference()
)

# First, ensure there is no ongoing change on the instance tree
# And ensure that current user can request the exact same instance tree
person.requestSoftwareInstance(**request_kw)
request_instance_tree = context.REQUEST.get('request_instance_tree')
if request_instance_tree.getRelativeUrl() != instance_tree.getRelativeUrl():
  redirect_error_kw['keep_items']['portal_status_message'] = Base_translateString('Not allowed to request this instance tree')
  return instance_tree.Base_redirect('view', **redirect_error_kw)

# Then, check if there is already an instance tree with this title
# XXX copy/pasted from requestSoftwareInstance
tag = "%s_%s_inProgress" % (actor.getUid(), title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  redirect_error_kw['keep_items']['portal_status_message'] = Base_translateString('Conflicts while renaming')
  return instance_tree.Base_redirect('view', **redirect_error_kw)

existing_instance_tree = portal.portal_catalog.getResultValue(
  portal_type=instance_tree.getPortalType(),
  title={'query': title, 'key': 'ExactMatch'},
  validation_state="validated",
  destination_section__uid=actor.getUid(),
)
if existing_instance_tree is not None:
  redirect_error_kw['keep_items']['portal_status_message'] = Base_translateString('There is an existing instance tree with this title')
  return instance_tree.Base_redirect('view', **redirect_error_kw)

# It should be safe to rename
root_instance = instance_tree.InstanceTree_getRootInstance()
instance_tree.edit(title=title)
# reindex with tag to prevent API call to generate race condition
instance_tree.reindexObject(activate_kw={'tag': tag})
if root_instance is not None:
  root_instance.rename(
    new_name=title,
    comment="Rename %s into %s" % (root_instance.getTitle(), title)
  )
  root_instance.reindexObject(activate_kw={'tag': tag})

return instance_tree.Base_redirect('view', keep_items={'portal_status_message': Base_translateString('Renamed.')})
