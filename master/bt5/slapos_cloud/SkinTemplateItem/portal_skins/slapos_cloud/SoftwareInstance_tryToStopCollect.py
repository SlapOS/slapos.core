from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

instance = context

if instance.getSlapState() != "start_requested":
  # Only continue if the instance is started
  return

instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")
if (instance_tree.getSlapState() == "stop_requested"):

  if instance.getPortalType() == 'Software Instance':
    is_slave = False
  elif instance.getPortalType() == 'Slave Instance':
    is_slave = True
  else:
    raise NotImplementedError("Unknown portal type %s of %s" % \
        (instance.getPortalType(), instance.getRelativeUrl()))

  # Buildout may not propagate the stop request
  requester = instance.getSuccessorRelatedValue()
  if requester is None:
    # Instance is orphan, so it stops itself.
    instance.requestStop(
      software_release=instance.getUrlString(),
      software_type=instance.getSourceReference(),
      instance_xml=instance.getTextContent(),
      sla_xml=instance.getSlaXml(),
      shared=is_slave,
      comment="Stop collect %s" % instance.getRelativeUrl())
  else:
    if (instance.getRelativeUrl() in requester.getSuccessorList()) and \
      (requester.getSlapState() == "stop_requested"):
       # For security, only stop if parent is also stopped
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
      # reset request cache
      # It is required to allow requested to start the instance again
      # XXX TODO: the cache handling must be fixed, as it is spreaded
      # in multiple places, which probably means there are other bugs like this
      requester.setLastData({}, key='_'.join([requester.getRelativeUrl(), instance.getTitle()]))
