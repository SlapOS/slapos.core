instance_node = context

if (context.getPortalType() != "Instance Node"):
  return
if instance_node.getValidationState() != 'validated':
  return

software_instance = instance_node.getSpecialiseValue(portal_type='Software Instance')
if (software_instance is not None) and (software_instance.getValidationState() == 'invalidated'):

  instance_node.invalidate(
    comment='The software instance %s was invalidated' % software_instance.getRelativeUrl()
  )
  instance_node.reindexObject(activate_kw=activate_kw)
