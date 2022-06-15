from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance_tree = context
assert instance_tree.getDefaultDestinationSection() == person_relative_url
person = instance_tree.getDefaultDestinationSectionValue()

slap_state = instance_tree.getSlapState()
if (slap_state in ['start_requested', 'stop_requested']):
  person.requestSoftwareInstance(
    state='destroyed',
    software_release=instance_tree.getUrlString(),
    software_title=instance_tree.getTitle(),
    software_type=instance_tree.getSourceReference(),
    instance_xml=instance_tree.getTextContent(),
    sla_xml=instance_tree.getSlaXml(),
    shared=instance_tree.isRootSlave(),
    project_reference=instance_tree.getFollowUpReference()
  )
  return True
return False
