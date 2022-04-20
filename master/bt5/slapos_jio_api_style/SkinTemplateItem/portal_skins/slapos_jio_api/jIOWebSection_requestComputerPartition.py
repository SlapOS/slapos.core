compute_node_id = data_dict.get("compute_node_id", None)
compute_partition_id = data_dict.get("compute_partition_id", None)

class SoftwareInstanceNotReady(Exception):
  pass

class NotFound(Exception):
  pass

class Unauthorized(Exception):
  pass

castToStr = context.Base_castDictToXMLString

def logError(e, error_name="", error_code=400, detail_list=None):
  return portal.ERP5Site_logApiErrorAndReturn(
    error_code=error_code,
    error_message=e,
    error_name=error_name,
    detail_list=detail_list,
  )

LOG = context.log

portal = context.getPortalObject()

def _assertACI(document):
  if context.Base_checkPermission(document.relative_url, 'View'):
    return document.getObject()
  raise Unauthorized('User has no access to %r' % (document.relative_url))


def getDocument(**kwargs):
  # No need to get all results if an error is raised when at least 2 objects
  # are found
  l = portal.portal_catalog.unrestrictedSearchResults(limit=2, select_list=("relative_url", "uid"), **kwargs)
  if len(l) != 1:
    raise NotFound, "No document found with parameters: %s" % kwargs
  else:
    return _assertACI(l[0])

def getNonCachedComputeNodeUidByReference(compute_node_reference):
  return portal.portal_catalog.unrestrictedSearchResults(
    portal_type='Compute Node', reference=compute_node_reference,
    validation_state="validated")[0].UID


def getComputePartitionDocument(compute_node_reference,
                                  compute_partition_reference):
  """
  Get the compute partition defined in an available compute_node
  """
  # Related key might be nice
  return getDocument(portal_type='Compute Partition',
                     reference=compute_partition_reference,
                     parent_uid=getNonCachedComputeNodeUidByReference(
                        compute_node_reference))


def getSoftwareInstanceForComputePartition(compute_node_id,
    compute_partition_id, slave_reference=None):
  compute_partition_document = getComputePartitionDocument(
    compute_node_id, compute_partition_id)
  if compute_partition_document.getSlapState() != 'busy':
    LOG('SlapTool::_getSoftwareInstanceForComputePartition'
        + 'Compute partition %s shall be busy, is free' %
        compute_partition_document.getRelativeUrl())
    raise NotFound, "No software instance found for: %s - %s" % (compute_node_id,
        compute_partition_id)
  else:
    query_kw = {
      'validation_state': 'validated',
      'portal_type': 'Slave Instance',
      'default_aggregate_uid': compute_partition_document.getUid(),
    }
    if slave_reference is None:
      query_kw['portal_type'] = "Software Instance"
    else:
      query_kw['reference'] = slave_reference

    software_instance = _assertACI(portal.portal_catalog.unrestrictedGetResultValue(**query_kw))
    if software_instance is None:
      raise NotFound, "No software instance found for: %s - %s" % (
        compute_node_id, compute_partition_id)
    else:
      return software_instance



# Loads partition parameter
partition_parameter = data_dict.get("parameters", {})
if isinstance(partition_parameter, str):
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
  #raise ValueError("%s" % kw)

  if compute_node_id and compute_partition_id:
    requester = getSoftwareInstanceForComputePartition(
      compute_node_id,
      compute_partition_id)
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

  if requested_software_instance is None:
    raise SoftwareInstanceNotReady
  else:
    if not requested_software_instance.getAggregate(portal_type="Compute Partition"):
      raise SoftwareInstanceNotReady
    else:
      return requested_software_instance.asJSONText()
except SoftwareInstanceNotReady:
  return logError(
    "Software Instance Not Ready",
    error_name="SoftwareInstanceNotReady",
    error_code=102
  )
except Unauthorized, log:
  return logError(
    log,
    error_code=401
  )
except NotFound, log:
  return logError(
    log,
    error_code=404
  )
