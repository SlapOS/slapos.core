"""
  Take the Text Content and adapt it as template for create
  an variation for a specific software release.

  This adapt the definition of KVM to instantiate multiple VMs instead a single
  for example.
"""
import json

parameter_text = context.getTextContent()
if not amount or parameter_text is None:
  return None

json_parameter = context.Base_instanceXmlToDict(parameter_text)
serialisation = "xml"

if "_" in json_parameter:
  # This is json-in-xml serialisation
  serialisation = "json-in-xml"
  json_parameter = json.loads(json_parameter["_"])
else:
  raise ValueError("KVM Cluster only supports serialised values!")

KVM1 = json_parameter["kvm-partition-dict"]["KVM1"]

for i in range(amount):
  json_parameter["kvm-partition-dict"]["KVM" + str(i)] = KVM1

xml_paramerter = """
  <?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">%s</parameter>
</instance>""" % json.dumps(json_parameter, indent=2)

return xml_paramerter
