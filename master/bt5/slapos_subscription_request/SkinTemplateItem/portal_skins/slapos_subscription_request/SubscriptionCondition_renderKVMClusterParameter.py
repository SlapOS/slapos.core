"""
  Take the Text Content and adapt it as template for create
  an variation for a specific software release.

  This adapt the definition of KVM to instantiate multiple VMs instead a single
  for example.
"""
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized
import json

parameter_text = context.getTextContent()
if not amount or parameter_text is None:
  return None

json_parameter = context.Base_instanceXmlToDict(parameter_text)

if "_" in json_parameter:
  # This is json-in-xml serialisation
  json_parameter = json.loads(json_parameter["_"])
else:
  raise ValueError("KVM Cluster only supports serialised values!")

KVM0 = json_parameter["kvm-partition-dict"]["KVM0"]

for i in range(amount):
  if i == 0:
    k = KVM0.copy()
    k["sticky-computer"] = True
    json_parameter["kvm-partition-dict"]["KVM" + str(i)] = k
  else:
    json_parameter["kvm-partition-dict"]["KVM" + str(i)] = KVM0

xml_parameter = """<?xml version="1.0" encoding="utf-8"?>
<instance>
    <parameter id="_">%s</parameter>
</instance>""" % json.dumps(json_parameter,
  indent=2,
  sort_keys=True,
  # BBB PY2 https://github.com/python/cpython/issues/60537#issuecomment-1093598422
  separators=(',', ': '),
)

return xml_parameter
