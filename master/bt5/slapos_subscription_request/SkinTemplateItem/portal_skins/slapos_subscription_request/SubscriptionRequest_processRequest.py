if context.getAggregate() is not None:
  return

person = context.getDestinationSectionValue()
if person is None:
  return

if context.getSimulationState() == "confirmed":
  return

request_kw = {}
default_xml = """<?xml version="1.0" encoding="utf-8"?>
<instance>
</instance>
"""

if context.getUrlString() is None:
  raise ValueError("url_string cannot be None")

request_kw.update(
    software_release=context.getUrlString(),
    # Bad title
    software_title=context.getTitle() + " %s" % str(context.getUid()),
    software_type=context.getSourceReference("default"),
    instance_xml=context.getTextContent(default_xml).strip(),
    sla_xml=context.getSlaXml(default_xml).strip(),
    shared=bool(context.getRootSlave(0)),
    state="started",
  )

person.requestSoftwareInstance(**request_kw)

requested_software_instance = context.REQUEST.get('request_instance')

if requested_software_instance is None:
  return

# Save the requested instance tree
context.setAggregate(requested_software_instance.getSpecialise())