from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance = context

if (instance.getSlapState() == "start_requested"):
  instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")
  if (instance_tree.getSlapState() == "stop_requested"):
    # Buildout may not propagate the stop request
    requester = instance.getSuccessorRelatedValue()
    if (instance.getRelativeUrl() in requester.getSuccessorList()) and \
      (requester.getSlapState() == "stop_requested"):
      # For security, only stop if parent is also stopped

      if instance.getPortalType() == 'Software Instance':
        is_slave = False
      elif instance.getPortalType() == 'Slave Instance':
        is_slave = True
      else:
        raise NotImplementedError, "Unknown portal type %s of %s" % \
          (instance.getPortalType(), instance.getRelativeUrl())

      requester.requestInstance(
        software_release=instance.getUrlString(),
        software_title=instance.getTitle(),
        software_type=instance.getSourceReference(),
        instance_xml=instance.getTextContent(),
        sla_xml=instance.getSlaXml(),
        shared=is_slave,
        state="stopped",
        comment="Stop collect %s" % instance.getRelativeUrl()
      )
