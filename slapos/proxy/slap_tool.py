from flask import request, Blueprint, current_app, abort
from .db import execute_db, requestInstanceFromDB, supplyFromDB, removeFromDB, \
                bangInstanceFromDB, freePartitionFromDB, formatFromDB, \
                NotFoundPartitionFailure, PartitionDeletionFailure, \
                getPartitionFromDB, AllocationFailure, ConfigurationError
from slapos.util import loads, dumps
from slapos.util import unicode2str, \
    xml2dict, dict2xml

from slapos.slap.slap import Computer, ComputerPartition, \
    SoftwareRelease, NotFoundError

slap_tool_blueprint = Blueprint('slap_tool', __name__)

EMPTY_DICT_XML = dumps({})

class UnauthorizedError(Exception):
  pass

def partitiondict2partition(partition):
  computer_id = partition['computer_reference']
  partition_id = partition['reference']
  slap_partition = ComputerPartition(computer_id, partition_id)
  slap_partition._software_release_document = None
  slap_partition._requested_state = 'destroyed'
  slap_partition._need_modification = 0
  slap_partition._instance_guid = '%(computer_reference)s-%(reference)s' \
    % partition

  if partition['software_release']:
    slap_partition._need_modification = 1
    slap_partition._requested_state = partition['requested_state']
    slap_partition._parameter_dict = xml2dict(partition['xml'])
    address_list = []
    full_address_list = []
    for address in execute_db('partition_network',
                              'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                              (partition_id, computer_id)):
      address_list.append((address['reference'], address['address']))
    slap_partition._parameter_dict['ip_list'] = address_list
    slap_partition._parameter_dict['full_address_list'] = full_address_list
    slap_partition._parameter_dict['slap_software_type'] = \
        partition['software_type']
    slap_partition._parameter_dict['instance_title'] = \
        partition['partition_reference']
    slap_partition._parameter_dict['root_instance_title'] = \
        partition['requested_by'] or partition['partition_reference']
    slap_partition._parameter_dict['slap_computer_id'] = \
        computer_id
    slap_partition._parameter_dict['slap_computer_partition_id'] = \
        partition_id
    slap_partition._parameter_dict['slap_software_release_url'] = \
        partition['software_release']

    if partition['slave_instance_list'] is not None:
      slap_partition._parameter_dict['slave_instance_list'] = \
          loads(partition['slave_instance_list'].encode('utf-8'))
    else:
      slap_partition._parameter_dict['slave_instance_list'] = []
    timestamp = partition['timestamp']
    if timestamp:
      slap_partition._parameter_dict['timestamp'] = str(timestamp)
    slap_partition._connection_dict = xml2dict(partition['connection_xml'])
    slap_partition._software_release_document = SoftwareRelease(
      software_release=partition['software_release'],
      computer_guid=computer_id)

  return slap_partition

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
      partition))
  return dumps(slap_computer)

@slap_tool_blueprint.route('/registerComputerPartition', methods=['GET'])
def registerComputerPartition():
  args = request.args
  partition = getPartitionFromDB(unicode2str(args['computer_partition_reference']),
                                 unicode2str(args['computer_reference']))
  if partition is None:
    raise UnauthorizedError
  return dumps(partitiondict2partition(partition))


@slap_tool_blueprint.route('/setComputerPartitionConnectionXml', methods=['POST'])
def setComputerPartitionConnectionXml():
  slave_reference = request.form.get('slave_reference', None)
  computer_partition_id = unicode2str(request.form['computer_partition_id'])
  computer_id = unicode2str(request.form['computer_id'])
  connection_xml = dict2xml(loads(request.form['connection_xml'].encode('utf-8')))
  if not slave_reference or slave_reference == 'None':
    query = 'UPDATE %s SET connection_xml=? WHERE reference=? AND computer_reference=?'
    argument_list = [connection_xml, computer_partition_id, computer_id]
    execute_db('partition', query, argument_list)
  else:
    query = 'UPDATE %s SET connection_xml=? , hosted_by=? WHERE reference=?'
    argument_list = [connection_xml, computer_partition_id, slave_reference]
    execute_db('slave', query, argument_list)
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
  requested_by = getRequesterFromForm(request.form, True)
  bangInstanceFromDB(requested_by, '')
  return 'OK'

@slap_tool_blueprint.route('/startedComputerPartition', methods=['POST'])
def startedComputerPartition():
  return 'Ignored'

@slap_tool_blueprint.route('/stoppedComputerPartition', methods=['POST'])
def stoppedComputerPartition():
  return 'Ignored'

@slap_tool_blueprint.route('/destroyedComputerPartition', methods=['POST'])
def destroyedComputerPartition():
  key = (unicode2str(request.form['computer_partition_id']),
         unicode2str(request.form['computer_id']))
  try:
    freePartitionFromDB(*key)
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
  parsed_request_dict = {
    'requester_id': unicode2str(request.form.get('computer_partition_id', 'user')),
    'requested_by': getRequesterFromForm(form) or '',
    'software_release': unicode2str(form['software_release']),
    'software_type': unicode2str(form['software_type']),
    'partition_reference': unicode2str(form['partition_reference']),
    'partition_parameter_kw': loads(form.get('partition_parameter_xml', EMPTY_DICT_XML).encode('utf-8')),
    'filter_kw': loads(form.get('filter_xml', EMPTY_DICT_XML).encode('utf-8')),
    # Note: currently ignored for slave instance (slave instances
    # are always started).
    'requested_state': loads(form['state'].encode('utf-8')),
    # Is it a slave instance?
    'slave': loads(form.get('shared_xml', EMPTY_DICT_XML).encode('utf-8'))
  }
  try:
    partition = requestInstanceFromDB(**parsed_request_dict)
  except (AllocationFailure, ConfigurationError) as e:
    return abort(404, str(e))
  if getattr(partition, '_request_dict', None) is not None:
    # ResourceNotReady
    return abort(408, 'Resource not ready')
  return dumps(partition)

def getRequesterFromForm(form, required=False):
  try:
    computer_id = form['computer_id']
    partition_id = form['computer_partition_id']
  except KeyError:
    if required:
      raise
    return
  partition = getPartitionFromDB(unicode2str(partition_id), unicode2str(computer_id))
  return partition and (partition['requested_by'] or
                        partition['partition_reference'])


@slap_tool_blueprint.route('/softwareInstanceRename', methods=['POST'])
def softwareInstanceRename():
  new_name = unicode2str(request.form['new_name'])
  key = (unicode2str(request.form['computer_partition_id']),
         unicode2str(request.form['computer_id']))
  partition = getPartitionFromDB(*key)
  if not partition:
    return "Unknown partition %r on %r" % key

  if not partition['requested_by']:
    execute_db(
      'partition',
      'UPDATE %s SET requested_by=? WHERE requested_by=?',
      (new_name, partition['partition_reference']))

  execute_db(
    'partition',
    'UPDATE %s SET partition_reference=?'
    ' WHERE reference=? AND computer_reference=?',
    (new_name,) + key)
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
