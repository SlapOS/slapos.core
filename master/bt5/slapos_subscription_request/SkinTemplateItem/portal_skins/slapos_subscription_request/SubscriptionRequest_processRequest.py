if context.getAggregate() is not None:
  return

person = context.getDestinationSectionValue()

if person is None:
  return

if context.getSimulationState() == "validated":
  return

request_kw = {}
request_kw.update(
    software_release=context.getUrlString(),
    # Bad title
    software_title=context.getTitle() + " %s" % str(context.getUid()),
    software_type=context.getSourceReference(),
    instance_xml=context.getTextContent().strip(),
    sla_xml=context.getSlaXml().strip(),
    shared=context.getRootSlave(),
    state="started",
  )

person.requestSoftwareInstance(**request_kw)

requested_software_instance = context.REQUEST.get('request_instance')

if requested_software_instance is None:
  return

# Save the requested hosting subscription
context.setAggregate(requested_software_instance.getSpecialise())
