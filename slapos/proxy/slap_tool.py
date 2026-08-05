from flask import request, Blueprint, current_app, abort, g
from .db import execute_db, requestInstanceFromDB, supplyFromDB, removeFromDB, \
                bangInstance, freePartitionFromDB, formatFromDB, \
                NotFoundPartitionFailure, PartitionDeletionFailure, \
                getPartitionFromDB, AllocationFailure, ConfigurationError, \
                identifyRequester, UnknownRequester, renameInstance, \
                setInstanceConnectionParameters, getRootInstanceTitle, \
                getSlaveInstanceList, _rowToSoftwareInstance
from slapos.util import loads, dumps
from slapos.util import unicode2str, \
    xml2dict, dict2xml

from slapos.slap.slap import Computer, ComputerPartition, SoftwareInstance, \
    SoftwareRelease, NotFoundError

slap_tool_blueprint = Blueprint('slap_tool', __name__)

EMPTY_DICT_XML = dumps({})

class UnauthorizedError(Exception):
  pass


def identify_requester_from_form():
  """Resolve the asserted requester identity once per slap_tool request.

  slap_tool asserts identity through its long-standing computer_id /
  computer_partition_id form fields. This stays LENIENT to preserve the
  deployed protocol's failure mode: an asserted but unresolvable identity is
  warned and treated as a direct user request, never a 4xx."""
  computer_id = request.form.get('computer_id')
  partition_id = request.form.get('computer_partition_id')
  # g.requester_id flows into the '%s_%s' forwarding prefix; decode the raw
  # form values for py2 (identity, guarded for the absent field).
  if computer_id is not None:
    computer_id = unicode2str(computer_id)
  if partition_id is not None:
    partition_id = unicode2str(partition_id)
  try:
    g.requester = identifyRequester(computer_id, partition_id)
  except UnknownRequester:
    current_app.logger.warning(
      'Unknown requester %r on %r asserted; treating request as user '
      '(legacy slap_tool leniency)', partition_id, computer_id)
    g.requester = None
  g.requester_id = partition_id or 'user'

slap_tool_blueprint.before_request(identify_requester_from_form)


def partitiondict2partition(partition, instance):
  """Build the slap_tool ComputerPartition wire object from a partition
  resource row and the non-shared instance allocated to it (or None).

  A free slot (no instance) reports itself destroyed and names itself by its
  partition address; an allocated slot publishes the instance's guid, its
  parameters/type/state/connection, and the derived slave_instance_list."""
  computer_id = partition['computer_reference']
  partition_id = partition['reference']
  slap_partition = ComputerPartition(computer_id, partition_id)
  slap_partition._software_release_document = None
  slap_partition._requested_state = 'destroyed'
  slap_partition._need_modification = 0

  if instance is None:
    slap_partition._instance_guid = '%s-%s' % (computer_id, partition_id)
    return slap_partition

  slap_partition._instance_guid = instance['instance_guid']
  slap_partition._need_modification = 1
  slap_partition._requested_state = instance['requested_state'] or 'started'
  slap_partition._parameter_dict = xml2dict(instance['xml'])
  address_list = []
  full_address_list = []
  for address in execute_db('partition_network',
                            'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                            (partition_id, computer_id)):
    address_list.append((address['reference'], address['address']))
  slap_partition._parameter_dict['ip_list'] = address_list
  slap_partition._parameter_dict['full_address_list'] = full_address_list
  slap_partition._parameter_dict['slap_software_type'] = \
      instance['software_type']
  slap_partition._parameter_dict['instance_title'] = \
      instance['title']
  slap_partition._parameter_dict['root_instance_title'] = \
      getRootInstanceTitle(instance)
  slap_partition._parameter_dict['slap_computer_id'] = \
      computer_id
  slap_partition._parameter_dict['slap_computer_partition_id'] = \
      partition_id
  slap_partition._parameter_dict['slap_software_release_url'] = \
      instance['software_release']
  slap_partition._parameter_dict['slave_instance_list'] = \
      getSlaveInstanceList(computer_id, partition_id)
  timestamp = instance['timestamp']
  if timestamp:
    slap_partition._parameter_dict['timestamp'] = str(timestamp)
  slap_partition._connection_dict = xml2dict(instance['connection_xml'])
  slap_partition._software_release_document = SoftwareRelease(
    software_release=instance['software_release'],
    computer_guid=computer_id)

  return slap_partition


def _allocatedInstance(computer_id, partition_id):
  """The non-shared instance allocated to a partition slot, or None."""
  return execute_db('instance',
    'SELECT * FROM %s'
    ' WHERE shared=0 AND allocated_computer=? AND allocated_partition=?',
    (computer_id, partition_id), one=True)

@slap_tool_blueprint.route('/getComputerInformation', methods=['GET'])
def getComputerInformation():
  # Kept only for backward compatiblity
  return getFullComputerInformation()


@slap_tool_blueprint.route('/getFullComputerInformation', methods=['GET'])
def getFullComputerInformation():
  computer_id = request.args['computer_id']
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    # Backward compatibility
    if computer_id != current_app.config['computer_id']:
      raise NotFoundError('%s is not registered.' % computer_id)
  slap_computer = Computer(computer_id)
  slap_computer._software_release_list = []
  for sr in execute_db('software', 'select * from %s WHERE computer_reference=?', [computer_id]):
    software_release = SoftwareRelease(
        software_release=sr['url'],
        computer_guid=computer_id)
    software_release._requested_state = sr['requested_state']
    slap_computer._software_release_list.append(software_release)
  slap_computer._computer_partition_list = []
  for partition in execute_db('partition', 'SELECT * FROM %s WHERE computer_reference=?', [computer_id]):
    slap_computer._computer_partition_list.append(partitiondict2partition(
      partition, _allocatedInstance(computer_id, partition['reference'])))
  return dumps(slap_computer)

@slap_tool_blueprint.route('/registerComputerPartition', methods=['GET'])
def registerComputerPartition():
  args = request.args
  computer_reference = unicode2str(args['computer_reference'])
  partition_reference = unicode2str(args['computer_partition_reference'])
  partition = getPartitionFromDB(partition_reference, computer_reference)
  if partition is None:
    raise UnauthorizedError
  return dumps(partitiondict2partition(
    partition, _allocatedInstance(computer_reference, partition_reference)))


@slap_tool_blueprint.route('/setComputerPartitionConnectionXml', methods=['POST'])
def setComputerPartitionConnectionXml():
  # Subject addressing (the partition/instance these parameters belong to), not
  # requester identity -- resolved per-endpoint from the form, not from g.
  slave_reference = request.form.get('slave_reference', None)
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])
  connection_dict = loads(request.form['connection_xml'].encode('utf-8'))
  if not slave_reference or slave_reference == 'None':
    instance = _allocatedInstance(computer_id, computer_partition_id)
  else:
    instance = execute_db('instance',
      'SELECT * FROM %s WHERE shared=1 AND slave_reference=?',
      (slave_reference,), one=True)
  if instance is not None:
    try:
      setInstanceConnectionParameters(instance['instance_guid'], connection_dict)
    except NotFoundPartitionFailure:
      # teardown race: a concurrent destroy committed between resolving the
      # instance and storing its parameters. The subject is gone; no-op.
      pass
  return 'done'

@slap_tool_blueprint.route('/buildingSoftwareRelease', methods=['POST'])
def buildingSoftwareRelease():
  return 'Ignored'

@slap_tool_blueprint.route('/destroyedSoftwareRelease', methods=['POST'])
def destroyedSoftwareRelease():
  removeFromDB(request.form['computer_id'], request.form['url'])
  return 'OK'

@slap_tool_blueprint.route('/availableSoftwareRelease', methods=['POST'])
def availableSoftwareRelease():
  return 'Ignored'

@slap_tool_blueprint.route('/softwareReleaseError', methods=['POST'])
def softwareReleaseError():
  return 'Ignored'

@slap_tool_blueprint.route('/softwareInstanceError', methods=['POST'])
def softwareInstanceError():
  return 'Ignored'

@slap_tool_blueprint.route('/softwareInstanceBang', methods=['POST'])
def softwareInstanceBang():
  # An unresolved identity is a 200 'OK' no-op, never a 4xx: a legacy client's
  # bang() does not catch HTTP errors, and a child banging while its root is
  # being destroyed (teardown race) is a benign no-op.
  if g.requester is None:
    return 'OK'
  try:
    bangInstance(g.requester['instance_guid'])
  except NotFoundPartitionFailure:
    # teardown race: the requester was destroyed between identity resolution
    # and the bang. A bang on a gone instance is a benign no-op.
    pass
  return 'OK'

@slap_tool_blueprint.route('/startedComputerPartition', methods=['POST'])
def startedComputerPartition():
  return 'Ignored'

@slap_tool_blueprint.route('/stoppedComputerPartition', methods=['POST'])
def stoppedComputerPartition():
  return 'Ignored'

@slap_tool_blueprint.route('/destroyedComputerPartition', methods=['POST'])
def destroyedComputerPartition():
  # Subject addressing (the partition reporting itself destroyed), not requester
  # identity -- resolved per-endpoint from the form, not from g.
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])
  try:
    freePartitionFromDB(computer_partition_id, computer_id)
  except (NotFoundPartitionFailure, PartitionDeletionFailure) as error:
    return str(error)

  return 'OK'

@slap_tool_blueprint.route('/useComputer', methods=['POST'])
def useComputer():
  return 'Ignored'

@slap_tool_blueprint.route('/loadComputerConfigurationFromXML', methods=['POST'])
def loadComputerConfigurationFromXML():
  xml = request.form['xml']
  computer_dict = loads(xml.encode('utf-8'))
  partition_list = []
  for input_partition in computer_dict['partition_list']:
    ip_list = []
    for input_address in input_partition['address_list']:
      ip_list.append({
        'ip-address': input_address['addr'],
        'netmask': input_address['netmask'],
        # keep "or input_partition['reference']" for backward compatibility in webrunner
        'network-interface': input_partition['tap']['name'] or input_partition['reference']
      })
    partition_list.append({
      'partition_id': input_partition['reference'],
      'ip_list': ip_list
    })
  formatFromDB(
    computer_dict['reference'],
    partition_list,
    computer_address=computer_dict['address'],
    computer_netmask=computer_dict['netmask']
  )
  return 'done'



@slap_tool_blueprint.route('/supplySupply', methods=['POST'])
def supplySupply():
  url = request.form['url']
  computer_id = request.form['computer_id']
  state = request.form['state']
  supplyFromDB(computer_id, url, state)
  return 'Supplied %r to be %s' % (url, state)


@slap_tool_blueprint.route('/requestComputerPartition', methods=['POST'])
def requestComputerPartition():
  form = request.form
  try:
    result = requestInstanceFromDB(
      requester=g.requester,
      requester_id=g.requester_id,
      software_release=unicode2str(form['software_release']),
      software_type=unicode2str(form['software_type']),
      partition_reference=unicode2str(form['partition_reference']),
      partition_parameter_kw=loads(form.get('partition_parameter_xml', EMPTY_DICT_XML).encode('utf-8')),
      filter_kw=loads(form.get('filter_xml', EMPTY_DICT_XML).encode('utf-8')),
      # Note: currently ignored for slave instance (slave instances
      # are always started).
      requested_state=loads(form['state'].encode('utf-8')),
      # Is it a slave instance?
      slave=loads(form.get('shared_xml', EMPTY_DICT_XML).encode('utf-8')))
  except (AllocationFailure, ConfigurationError) as e:
    return abort(404, str(e))
  if isinstance(result, ComputerPartition):
    if getattr(result, '_request_dict', None) is not None:
      # ResourceNotReady
      return abort(408, 'Resource not ready')
    # frontend-bypass / external-master forward partition
    return dumps(result)
  if result is None:
    # A first-ever shared request with state 'destroyed' allocated nothing;
    # return an empty SoftwareInstance the old client can parse without error.
    return dumps(SoftwareInstance(
      slap_computer_id='', slap_computer_partition_id=''))
  # A local instance row: slap_tool's wire object omits _instance_guid for
  # shared rows (an old client's getInstanceGuid() on a shared partition keeps
  # its behaviour).
  return dumps(_rowToSoftwareInstance(result))


@slap_tool_blueprint.route('/softwareInstanceRename', methods=['POST'])
def softwareInstanceRename():
  # Subject addressing (the partition whose instance is renamed), not requester
  # identity -- resolved per-endpoint from the form, not from g.
  new_name = unicode2str(request.form['new_name'])
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])
  instance = _allocatedInstance(computer_id, computer_partition_id)
  if instance is None:
    return "Unknown partition %r on %r" % (computer_partition_id, computer_id)
  try:
    renameInstance(instance['instance_guid'], new_name)
  except NotFoundPartitionFailure:
    # teardown race: a concurrent destroy committed between resolving the
    # instance and the rename. Report the subject missing, as for None above.
    return "Unknown partition %r on %r" % (computer_partition_id, computer_id)
  return 'done'

@slap_tool_blueprint.route('/getComputerPartitionStatus', methods=['GET'])
def getComputerPartitionStatus():
  return dumps('Not implemented.')

@slap_tool_blueprint.route('/computerBang', methods=['POST'])
def computerBang():
  return dumps('')

@slap_tool_blueprint.route('/getComputerPartitionCertificate', methods=['GET'])
def getComputerPartitionCertificate():
  # proxy does not use partition certificate, but client calls this.
  return dumps({'certificate': '', 'key': ''})

@slap_tool_blueprint.route('/getSoftwareReleaseListFromSoftwareProduct', methods=['GET'])
def getSoftwareReleaseListFromSoftwareProduct():
  software_product_reference = request.args.get('software_product_reference')
  software_release_url = request.args.get('software_release_url')

  if software_release_url:
    assert(software_product_reference is None)
    raise NotImplementedError('software_release_url parameter is not supported yet.')
  else:
    assert(software_product_reference is not None)
    if software_product_reference in current_app.config['software_product_list']:
      software_release_url_list =\
          [current_app.config['software_product_list'][software_product_reference]]
    else:
      software_release_url_list = []
    return dumps(software_release_url_list)
