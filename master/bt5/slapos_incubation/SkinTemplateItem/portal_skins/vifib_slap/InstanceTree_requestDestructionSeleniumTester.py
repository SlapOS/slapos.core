from DateTime import DateTime
portal = context.getPortalObject()
instance_tree = context

now = DateTime()

if instance_tree.getDestinationSectionValue().getReference() == 'seleniumtester' and \
  instance_tree.getModificationDate() < (now - 1):

  person = instance_tree.getDestinationSectionValue(portal_type="Person")
  person.requestSoftwareInstance(
    software_release=instance_tree.getUrlString(),
    instance_xml=instance_tree.getTextContent(),
    software_type=instance_tree.getSourceReference(),
    sla_xml=instance_tree.getSlaXml(),
    shared=instance_tree.getRootSlave(),
    state="destroyed",
    software_title=instance_tree.getTitle(),
    comment='Requested by clenaup alarm', 
    activate_kw={'tag': tag}
  )
