from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance_tree = context
assert instance_tree.getDefaultDestinationSection() == person_relative_url
person = instance_tree.getDefaultDestinationSectionValue()

slap_state = instance_tree.getSlapState()
if (slap_state == 'start_requested'):
  person.requestSoftwareInstance(
    state='stopped',
    software_release=instance_tree.getUrlString(),
    software_title=instance_tree.getTitle(),
    software_type=instance_tree.getSourceReference(),
    instance_xml=instance_tree.getTextContent(),
    sla_xml=instance_tree.getSlaXml(),
    shared=instance_tree.isRootSlave()
  )
  return True
return False
