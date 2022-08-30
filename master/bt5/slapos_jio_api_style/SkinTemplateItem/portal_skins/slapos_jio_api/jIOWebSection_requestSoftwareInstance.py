compute_node_id = data_dict.get("compute_node_id", None)
compute_partition_id = data_dict.get("compute_partition_id", None)

class SoftwareInstanceNotReady(Exception):
  pass

castToStr = context.Base_castDictToXMLString

def logError(e, error_name="", error_code=400, detail_list=None):
  return portal.ERP5Site_logApiErrorAndReturn(
    error_code=error_code,
    error_message=e,
    error_name=error_name,
    detail_list=detail_list,
  )

portal = context.getPortalObject()

# Loads partition parameter
partition_parameter = data_dict.get("parameters", None)
if partition_parameter:
  import json
  try:
    partition_parameter = json.loads(partition_parameter)
  except ValueError, e:
    return logError(
      "Cannot Decode JSON Parameter. Error: %s" % e,
      error_name="CANNOT-DECODE-COMPUTER-PARTITION-JSON-PARAMETER",
    )

  if not isinstance(partition_parameter, dict):
    return logError(
      "Parameters should be a key value object.",
      error_name="INCORRECT-COMPUTER-PARTITION-JSON-PARAMETER",
    )
else:
  partition_parameter = {}

try:
  # filter dict
  filter_kw = data_dict.get("sla_parameters", {})

  partition_reference = data_dict.get("title")

  kw = dict(software_release=data_dict.get("software_release_uri"),
            software_type=data_dict.get("software_type", "RootSoftwareInstance"),
            software_title=partition_reference,
            instance_xml=castToStr(partition_parameter),
            shared=data_dict.get("shared", False),
            sla_xml=castToStr(filter_kw),
            state=data_dict.get("state", "started"))

  if compute_node_id and compute_partition_id:
    compute_partition = portal.portal_catalog.getComputePartitionObject(
      compute_node_id,
      compute_partition_id,
    )
    requester = compute_partition.getSoftwareInstance()
    instance_tree = requester.getSpecialiseValue()
    if instance_tree is not None and instance_tree.getSlapState() == "stop_requested":
      kw['state'] = 'stopped'
    key = '_'.join([instance_tree.getRelativeUrl(), partition_reference])
  else:
    # requested as root, so done by human
    requester = portal.portal_membership.getAuthenticatedMember().getUserValue()
    key = '_'.join([requester.getRelativeUrl(), partition_reference])

  last_data = requester.getLastData(key)
  requested_software_instance = None
  value = dict(
    hash='_'.join([requester.getRelativeUrl(), str(kw)]),
    )

  if last_data is not None and isinstance(last_data, type(value)):
    requested_software_instance = portal.restrictedTraverse(
        last_data.get('request_instance'), None)

  if last_data is None or not isinstance(last_data, type(value)) or \
    last_data.get('hash') != value['hash'] or \
    requested_software_instance is None:
    if compute_node_id and compute_partition_id:
      requester.requestInstance(**kw)
    else:
      # requester is a person so we use another method
      requester.requestSoftwareInstance(**kw)
    requested_software_instance = context.REQUEST.get('request_instance')
    if requested_software_instance is not None:
      value['request_instance'] = requested_software_instance\
        .getRelativeUrl()
      requester.setLastData(value, key=key)

  if requested_software_instance is not None:
    return requested_software_instance.asJSONText()
  raise SoftwareInstanceNotReady
except SoftwareInstanceNotReady:
  return logError(
    "Software Instance Not Ready",
    error_name="SoftwareInstanceNotReady",
    error_code=102
  )
