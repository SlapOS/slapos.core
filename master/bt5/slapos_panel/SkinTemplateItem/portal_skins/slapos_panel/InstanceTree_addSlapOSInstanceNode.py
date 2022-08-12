from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
instance_tree = context
software_instance = instance_tree.getSuccessorValue(portal_type='Software Instance')

# If an Instance Node already exist, do nothing
instance_node = portal.portal_catalog.getResultValue(
  portal_type="Instance Node",
  specialise__uid=software_instance.getUid()
)
if (instance_node is not None):
  return instance_node.Base_redirect(
    keep_items={
      'portal_status_message': translateString('Instance Node already created.')
    }
  )

# If an Instance Node is not yet indexed, do nothing
tag = "%s_createInstanceNode" % instance_tree.getUid()
if (0 < portal.portal_activities.countMessageWithTag(tag)):
  # The instance node is already under creation but can not be fetched from catalog
  return instance_tree.Base_redirect(
    keep_items={
      'portal_status_message': translateString('New Instance Node under creation.')
    }
  )


instance_node = portal.compute_node_module.newContent(
  portal_type='Instance Node',
  title=instance_tree.getTitle(),
  specialise_value=software_instance,
  follow_up_value=software_instance.getFollowUpValue(),
  activate_kw={'tag': tag}
)
instance_node.validate()

return instance_node.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Instance Node created.')
  }
)
