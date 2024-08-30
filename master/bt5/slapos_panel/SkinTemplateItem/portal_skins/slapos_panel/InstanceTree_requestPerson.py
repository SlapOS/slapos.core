if instance_xml is None:
  instance_xml = context.getTextContent()
if software_type is None:
  software_type = context.getSourceReference()
if state is None:
  state = {'start_requested': 'started',
           'destroy_requested': 'destroyed',
           'stop_requested': 'stopped'}[context.getSlapState()]

context.InstanceTree_updateParameterAndRequest(
  state=state,
  software_release=context.getUrlString(),
  software_title=context.getTitle(),
  software_type=software_type,
  instance_xml=instance_xml,
  sla_xml=context.getSlaXml(),
  shared=context.isRootSlave()
)
