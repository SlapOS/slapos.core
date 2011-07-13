from flask import g, Flask, request, abort, json
import xml_marshaller.xml_marshaller
from lxml import etree
import sqlite3

app = Flask(__name__)
DB_VERSION = app.open_resource('schema.sql').readline().strip().split(':')[1]

class UnauthorizedError(Exception):
  pass

def xml2dict(xml):
  result_dict = {}
  if xml is not None and xml != '':
    tree = etree.fromstring(xml.encode('utf-8'))
    for element in tree.iter(tag=etree.Element):
      if element.tag == 'parameter':
        key = element.get('id')
        value = result_dict.get(key, None)
        if value is not None:
          value = value + ' ' + element.text
        else:
          value = element.text
        result_dict[key] = value
  return result_dict

def partitiondict2partition(partition):
  # XXX-Cedric : change function name, as it does no longer create a
  # Partition instance, but rather create a dict ready to be sent in json
  slap_partition = dict(computer_id=app.config['computer_id'],
                        computer_partition_id=partition['reference'],
                        requested_state='started',
                        partition_reference=partition['partition_reference'])
  if partition['software_release']:
    slap_partition['need_modification'] = 1
  else:
    slap_partition['need_modification'] = 0
  # XXX-Cedric : do we have to load a json into dict? It will be changed back to json anyway.
  # XXX-Cedric : change from partition['xml'] to partition['json']
  parameter_dict = dict()
  if partition['xml']:
    parameter_dict = json.loads(partition['xml'])
  slap_partition['parameter_dict'] = parameter_dict
  address_list = []
  #XXX-Cedric : I do not understand the query. It is unclear what is partition['reference'], is it computer_partition_id or partition_reference?
  for address in execute_db('partition_network', 'SELECT * FROM %s WHERE partition_reference=?', [partition['reference']]):
    address_list.append((address['reference'], address['address']))
  slap_partition['parameter_dict']['ip_list'] = address_list
  slap_partition['parameter_dict']['software_type'] = partition['software_type']
  # XXX-Cedric: same here
  connection_dict = None
  if partition['connection_xml']:
    connection_dict = xml2dict(partition['connection_xml'])
  slap_partition['connection_dict'] = connection_dict
  slap_partition['software_release'] = partition['software_release']
  return slap_partition

def execute_db(table, query, args=(), one=False):
  try:
    cur = g.db.execute(query % (table + DB_VERSION,), args)
  except:
    app.logger.error('There was some issue during processing query %r on table %r with args %r' % (query, table, args))
    raise

  rv = [dict((cur.description[idx][0], value)
    for idx, value in enumerate(row)) for row in cur.fetchall()]
  return (rv[0] if rv else None) if one else rv

def connect_db():
  return sqlite3.connect(app.config['DATABASE_URI'])

@app.before_request
def before_request():
  g.db = connect_db()
  schema = app.open_resource('schema.sql')
  schema = schema.read() % dict(version = DB_VERSION)
  g.db.cursor().executescript(schema)
  g.db.commit()

@app.after_request
def after_request(response):
  g.db.commit()
  g.db.close()
  return response

@app.route('/<computer_id>', methods=['GET'])
def getComputerInformation(computer_id):
  """Returns information about computer"""
  if app.config['computer_id'] == computer_id:
    slap_computer = dict(computer_id = computer_id,
                         software_release_list = [],
                         computer_partition_list = [])
    for sr in execute_db('software', 'select * from %s'):
      slap_computer['software_release_list'].append(dict(
        software_release=sr['url'], computer_guid=computer_id))
    for partition in execute_db('partition', 'SELECT * FROM %s'):
      slap_computer['computer_partition_list'].append(
          partitiondict2partition(partition))
    return json.dumps(slap_computer)
  else:
    raise UnauthorizedError, "Only accept request for: %s" % \
                             app.config['computer_id']

@app.route('/<computer_id>/partition/<computer_partition_id>', methods=['POST'])
def setComputerPartitionConnectionJson(computer_id, computer_partition_id):
  # XXX-Cedric : change connection_xml to connection_json in sql
  query = 'UPDATE %s SET connection_xml=? WHERE reference=?'
  argument_list = [request.json, computer_partition_id.encode()]
  execute_db('partition', query, argument_list)
  return 'done'

@app.route('/<computer_id>/software/building', methods=['POST'])
@app.route('/<computer_id>/software/available', methods=['POST'])
def software_release_ignored_api(computer_id):
  url = request.form['url']
  return 'Ignored'

@app.route('/<computer_id>/software/error', methods=['POST'])
def softwareReleaseError(computer_id):
  return 'Ignored'

@app.route('/<computer_id>/partition/<computer_partition_id>/error', methods=['POST'])
def softwareInstanceError(computer_id, computer_partition_id):
  error_log = request.form['error_log']
  return 'Ignored'

@app.route('/<computer_id>/partition/<computer_partition_id>/building', methods=['POST'])
@app.route('/<computer_id>/partition/<computer_partition_id>/available', methods=['POST'])
@app.route('/<computer_id>/partition/<computer_partition_id>/started', methods=['POST'])
@app.route('/<computer_id>/partition/<computer_partition_id>/stopped', methods=['POST'])
@app.route('/<computer_id>/partition/<computer_partition_id>/destroyed', methods=['POST'])
def computer_partition_ignored_api(computer_id, computer_partition_id):
  return 'Ignored'

#@app.route('/partition/<partition_reference>', methods=['PUT'])
@app.route('/partition', methods=['POST'])
def requestComputerPartition(partition_reference = ''):
  """Request the creation of a computer partition"""
  request_dict = request.json
  software_release = request_dict['software_release'].encode()
  # some supported parameters
  software_type = request_dict.get('software_type', 'RootSoftwareInstance')
  if (software_type is None):
    software_type = 'RootSoftwareInstance'
  software_type = software_type.encode()
  if partition_reference is '':
    partition_reference = request_dict.get('partition_reference', '').encode()
  partition_id = request_dict.get('computer_partition_id', '')
  if (partition_id is None):
    partition_id = ''
  partition_id = partition_id.encode()
  parameter_dict_kw = request_dict.get('parameter_dict', None)
  if parameter_dict_kw:
    # In the future, parameter_dict will come either in xml or in json.
    # We will check it with schema.
    parameter_dict_kw = json.dumps(parameter_dict_kw).encode()
  instance_json = parameter_dict_kw
  args = []
  a = args.append
  q = 'SELECT * FROM %s WHERE software_release=?'
  a(software_release)
  if software_type:
    q += ' AND software_type=?'
    a(software_type)
  if partition_reference:
    q += ' AND partition_reference=?'
    a(partition_reference)
  if partition_id:
    q += ' AND requested_by=?'
    a(partition_id)
  partition = execute_db('partition', q, args, one=True)
  if partition is None:
    partition = execute_db('partition',
        'SELECT * FROM %s WHERE slap_state="free"', (), one=True)
    if partition is None:
      app.logger.warning('No more free computer partition')
      abort(408)
  args = []
  a = args.append
  q = 'UPDATE %s SET software_release=?, slap_state="busy"'
  a(software_release)
  if software_type:
    q += ' ,software_type=?'
    a(software_type)
  if partition_reference:
    q += ' ,partition_reference=?'
    a(partition_reference)
  if partition_id:
    q += ' ,requested_by=?'
    a(partition_id)
  if instance_json:
    # XXX-Cedric : change xml to sjon in sql
    q += ' ,xml=?'
    a(instance_json)
  q += ' WHERE reference=?'
  a(partition['reference'].encode())
  execute_db('partition', q, args)
  args = []
  partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=?',
      [partition['reference'].encode()], one=True)
  address_list = []
  for address in execute_db('partition_network', 'SELECT * FROM %s WHERE partition_reference=?', [partition['reference']]):
    address_list.append((address['reference'], address['address']))
  return json.dumps(dict(
    # XXX-Cedric : change xml to json in sql
    # XXX-Cedric : change this to return something that looks like a computer partition
    xml=partition['xml'],
    connection_xml=partition['connection_xml'],
    partition_reference=partition['partition_reference'],
    slap_computer_id=app.config['computer_id'],
    slap_computer_partition_id=partition['reference'],
    slap_software_release_url=partition['software_release'],
    slap_server_url='slap_server_url',
    software_type=partition['software_type'],
    slave_id_list=[],
    ip_list=address_list
    ))
  abort(408)
  computer_id = request.form.get('computer_id')
  computer_partition_id = request.form.get('computer_partition_id')
  software_type = request.form.get('software_type')
  partition_reference = request.form.get('partition_reference')
  shared = request.form.get('shared')
  parameter_dict = request.form.get('parameter_dict')
  filter_json = request.form.get('filter_json')
  raise NotImplementedError

@app.route('/<computer_id>/usage', methods=['POST'])
def useComputer(computer_id):
  use_string = request.form['use_string']
  return 'Ignored'

@app.route('/loadComputerConfigurationFromXML', methods=['POST'])
def loadComputerConfigurationFromXML():
  xml = request.form['xml']
  computer_dict = xml_marshaller.xml_marshaller.loads(str(xml))
  if app.config['computer_id'] == computer_dict['reference']:
    execute_db('computer', 'INSERT OR REPLACE INTO %s values(:address, :netmask)',
        computer_dict)
    for partition in computer_dict['partition_list']:

      execute_db('partition', 'INSERT OR IGNORE INTO %s (reference) values(:reference)', partition)
      execute_db('partition_network', 'DELETE FROM %s WHERE partition_reference = ?', [partition['reference']])
      for address in partition['address_list']:
        address['reference'] = partition['tap']['name']
        address['partition_reference'] = partition['reference']
        execute_db('partition_network', 'INSERT OR REPLACE INTO %s (reference, partition_reference, address, netmask) values(:reference, :partition_reference, :addr, :netmask)', address)

    return 'done'
  else:
    raise UnauthorizedError, "Only accept request for: %s" % \
                             app.config['computer_id']

#XXX-Cedric : We still use XML for formatting for now. 
#@app.route('/loadComputerConfiguration', methods=['POST'])
#def loadComputerConfigurationFromJson():
#  json_document = request.form['json']
#  computer_dict = json.loads(str(json_document))
#  if app.config['computer_id'] == computer_dict['reference']:
#    args = []
#    a = args.append
#    execute_db('computer', 'INSERT OR REPLACE INTO %s values(:address, :netmask)',
#        computer_dict)
#    for partition in computer_dict['partition_list']:
#
#      execute_db('partition', 'INSERT OR IGNORE INTO %s (reference) values(:reference)', partition)
#      execute_db('partition_network', 'DELETE FROM %s WHERE partition_reference = ?', [partition['reference']])
#      for address in partition['address_list']:
#        address['reference'] = partition['tap']['name']
#        address['partition_reference'] = partition['reference']
#        execute_db('partition_network', 'INSERT OR REPLACE INTO %s (reference, partition_reference, address, netmask) values(:reference, :partition_reference, :addr, :netmask)', address)
#
#    return 'done'
#  else:
#    raise UnauthorizedError, "Only accept request for: %s" % \
#                             app.config['computer_id']

@app.route('/<computer_reference>/partition/<partition_reference>', methods=['GET'])
def registerComputerPartition(computer_reference, partition_reference):
  if app.config['computer_id'] == computer_reference:
    partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=?',
      [partition_reference.encode()], one=True)
    if partition is None:
      raise UnauthorizedError
    return json.dumps(partitiondict2partition(partition))
  else:
    raise UnauthorizedError, "Only accept request for: %s" % \
                             app.config['computer_id']

@app.route('/<computer_id>/software', methods=['POST'])
def supplySupply(computer_id):
  url = request.json['url']
  if app.config['computer_id'] == computer_id:
    execute_db('software', 'INSERT OR REPLACE INTO %s VALUES(?)', [url])
  else:
    raise UnauthorizedError, "Only accept request for: %s" % \
                             app.config['computer_id']
  return '%r added' % url
