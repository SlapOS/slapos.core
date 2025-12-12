from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import NotAcceptable
from flask import current_app, request, abort, Blueprint, make_response, g, url_for
from .db import execute_db, requestInstanceFromDB, supplyFromDB, removeFromDB, \
                bangInstanceFromDB, getPartitionFromDB, freePartitionFromDB, \
                formatFromDB, \
                NotFoundPartitionFailure, PartitionDeletionFailure, \
                AllocationFailure, getInstanceTreeList, getAllocatedInstance
from slapos.util import dict2xml, xml2dict, loads
from slapos.slap.slap import ComputerPartition, SoftwareInstance
import json
import jsonschema
import sys


json_rpc_blueprint = Blueprint('json_rpc', __name__)
json_rpc_experimental_blueprint = Blueprint('json_rpc_experimental', __name__)


def find_best_match(status_code=None):
  if (status_code == 406) or (len(request.accept_mimetypes) == 0):
    mime = 'application/json'
  else:
    mime = request.accept_mimetypes.best_match(['application/json'])
    if mime is None:
      # Didn't find good mimetype.
      raise NotAcceptable
  return mime


def send_json_rpc_document(json_rpc_dict, status_code=None, mime=None):
  if mime is None:
    try:
      mime = find_best_match(status_code=status_code)
    except NotAcceptable:
      return current_app.handle_http_exception(NotAcceptable)

  data = json.dumps(json_rpc_dict)
  if status_code:
    rv = make_response((data, status_code))
  else:
    rv = make_response(data)

  rv.headers['Content-Type'] = mime
  return rv


def validate_and_send_json_rpc_document(json_rpc_dict, **kw):
  output_schema_text = g.output_schema_text
  # validate output
  try:
    jsonschema.validate(
      json_rpc_dict,
      output_schema_text,
      format_checker=jsonschema.FormatChecker()
    )
  except jsonschema.exceptions.ValidationError as err:
    return abort(500, err.message)

  return send_json_rpc_document(json_rpc_dict, **kw)


def before_request(open_api_json_file_name):
  if (request.method != "POST"):
    return abort(405)

  # Validate the input json
  with json_rpc_blueprint.open_resource(open_api_json_file_name, 'r') as json_rpc_open_api_file:
    config_filejson_rpc_parsed_json = json.loads(json_rpc_open_api_file.read())

  try:
    method = config_filejson_rpc_parsed_json['paths'][request.path]['post']
  except KeyError:
    return abort(500, '%s is not part of the open api definition' % request.path)

  input_schema_text = method['requestBody']['content']['application/json']['schema']
  g.output_schema_text = method['responses']['200']['content']['application/json']['schema']

  # Validate the input body
  body_json = request.json
  try:
    jsonschema.validate(
      body_json,
      input_schema_text,
      format_checker=jsonschema.FormatChecker()
    )
  except jsonschema.exceptions.ValidationError as err:
    return abort(400, err.message)

def before_json_rpc_request():
  return before_request('json_rpc.json')

def before_json_rpc_experimental_request():
  return before_request('json_rpc_experimental.json')

json_rpc_blueprint.before_request(before_json_rpc_request)
json_rpc_experimental_blueprint.before_request(before_json_rpc_experimental_request)


class JsonRpcManager(object):
  '''
  This object is used to replicate the slapos master json rpc api
  '''
  def init_app(self, app, **kw):
    app.register_blueprint(json_rpc_blueprint, **kw)
    app.register_blueprint(json_rpc_experimental_blueprint, **kw)
    app.handle_exception = self._custom_handle_exception
    app.handle_http_exception = self._custom_handle_http_exception

  # Redefine http exception handling to return JSON
  def _custom_handle_http_exception(self, exception):
    if request.blueprint in ['json_rpc', 'json_rpc_experimental']:
      error_dict = {
        "status": exception.code,
        "type": HTTP_STATUS_CODES.get(exception.code, 'Unknown Error'),
        "title": exception.description
      }
      return send_json_rpc_document(error_dict, status_code=exception.code)
    return exception

  # Redefine python exception handling to return JSON
  def _custom_handle_exception(self, exception):
    if request.blueprint in ['json_rpc', 'json_rpc_experimental']:
      # Log exception and return json
      exc_type, exc_value, tb = sys.exc_info()
      current_app.log_exception((exc_type, exc_value, tb))
      return send_json_rpc_document({
        'status': 500,
        'type': HTTP_STATUS_CODES.get(500, 'Unknown Error'),
        'title': 'Internal server error'
      }, status_code=500)
    raise exception


@json_rpc_blueprint.route('/slapos.remove.v0.compute_node_certificate', methods=['POST'])
def remove_compute_node_certificate():
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Ignored'
  })

@json_rpc_blueprint.route('/slapos.post.v0.software_installation', methods=['POST'])
def supply_software_installation():
  computer_id = request.json["computer_guid"]
  software_release_uri = request.json["software_release_uri"]
  state = request.json.get("state", "available")
  supplyFromDB(computer_id, software_release_uri, state)
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Supplied %s to be %s' % (software_release_uri, state)
  })

@json_rpc_blueprint.route('/slapos.post.v0.compute_node_usage', methods=['POST'])
def post_compute_node_usage():
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Ignored'
  })

@json_rpc_blueprint.route('/slapos.post.v0.compute_node_certificate', methods=['POST'])
def post_compute_node_certificate():
  # proxy does not use node certificate, but client calls this.
  return validate_and_send_json_rpc_document({
    'key': '',
    'certificate': ''
  })

@json_rpc_blueprint.route('/slapos.allDocs.v0.compute_node_software_installation_list', methods=['POST'])
def compute_node_software_installation_list():
  computer_id = request.json["computer_guid"]
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    return abort(403, '%s is not registered.' % computer_id)
  software_release_list = []
  for sr in execute_db('software', 'select * from %s WHERE computer_reference=?', [computer_id]):
    software_release_list.append({
      'software_release_uri': sr['url'],
      'state': sr['requested_state']
    })
  return validate_and_send_json_rpc_document({
    'result_list': software_release_list
  })

def generateInstanceGuid(title, requested_by, is_shared):
  # We expect slapproxy to only a uniq partition_reference/requested_by
  return '%s___%s___%i' % (title, requested_by, int(is_shared))

def extractInstanceGuid(instance_guid):
  result_list = instance_guid.split('___', 2)
  result_list[2] = bool(int(result_list[2]))
  return result_list

def generateDBSlaveReference(title, requested_by):
  return '%s_%s' % (requested_by, title)

def extractDBSlaveReference(reference):
  requested_by, title = reference.split('_', 1)
  return title, requested_by


@json_rpc_blueprint.route('/slapos.allDocs.v0.compute_node_instance_list', methods=['POST'])
def compute_node_instance_list():
  computer_id = request.json["computer_guid"]
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    return abort(403, '%s is not registered.' % computer_id)
  instance_list = []
  for partition in execute_db('partition', 'SELECT * FROM %s WHERE computer_reference=? AND slap_state="busy"', [computer_id]):
    instance_list.append({
      "title": partition['partition_reference'],
      "instance_guid": generateInstanceGuid(partition['partition_reference'], partition['requested_by'], False),
      "state": partition['requested_state'],
      "compute_partition_id": partition['reference'],
      "software_release_uri": partition['software_release'],
    })
  return validate_and_send_json_rpc_document({
    'result_list': instance_list
  })

@json_rpc_blueprint.route('/slapos.allDocs.v0.instance_node_instance_list', methods=['POST'])
def instance_node_instance_list():
  try:
    partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
  except (ValueError, IndexError):
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])

  partition = getAllocatedInstance(partition_reference, requested_by)
  if is_shared or (not partition):
    return abort(403, 'No software instance %s found.' % request.json["instance_guid"])

  result_list = []
  slave_instance_list = []
  if partition['slave_instance_list'] is not None:
    slave_instance_list = loads(partition['slave_instance_list'].encode('utf-8'))
  for slave_information in slave_instance_list:
    title, asked_by = extractDBSlaveReference(slave_information.pop('slave_title'))
    # Drop added informations
    slap_software_type = slave_information.pop('slap_software_type')
    slave_information.pop('slave_reference')
    result_list.append({
      "title": title,
      "instance_guid": generateInstanceGuid(title, asked_by, True),
      "software_type": slap_software_type,
      # The state is not stored in slapproxy
      "state": "started",
      "parameters": slave_information,
      "compute_partition_id": partition['reference']
    })
  return validate_and_send_json_rpc_document({
    'result_list': result_list
  })

@json_rpc_blueprint.route('/slapos.get.v0.hateoas_url', methods=['POST'])
def get_hateoas_url():
  return validate_and_send_json_rpc_document({
    'hateoas_url': url_for('hateoas.hateoas', _external=True)
  })

@json_rpc_blueprint.route('/slapos.get.v0.compute_node_status', methods=['POST'])
def get_compute_node_status():
  return validate_and_send_json_rpc_document({
    'text': 'Unknown (not implemented)'
  })

@json_rpc_blueprint.route('/slapos.get.v0.software_instance_certificate', methods=['POST'])
def get_software_instance_certificate():
  # proxy does not use partition certificate, but client calls this.
  return validate_and_send_json_rpc_document({
    'key': '',
    'certificate': ''
  })

def send_json_rpc_sql_partition(partition):
  address_list = []
  for address in execute_db('partition_network',
                            'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                            (partition['reference'], partition['computer_reference'])):
    address_list.append([address['reference'], address['address']])

  return validate_and_send_json_rpc_document({
    "title": partition['partition_reference'],
    "instance_guid": generateInstanceGuid(partition['partition_reference'], partition['requested_by'], False),
    "software_release_uri": partition['software_release'],
    "software_type": partition['software_type'],
    "state": partition['requested_state'],
    "connection_parameters": xml2dict(partition['connection_xml']),
    "parameters": xml2dict(partition['xml']),
    "shared": False,
    "root_instance_title": partition['requested_by'] or partition['partition_reference'],
    "ip_list": address_list,
    "full_ip_list": [],
    # sla are not stored in slapproxy
    "sla_parameters": {},
    "computer_guid": partition['computer_reference'],
    "compute_partition_id": partition['reference'],
    "processing_timestamp": int(partition['timestamp'] or '0'),
    # This info is probably not available
    "access_status_message": ''
  })


def send_json_rpc_sql_shared(shared_instance, partition):
  title, asked_by = extractDBSlaveReference(shared_instance['reference'])
  assert asked_by == shared_instance['asked_by']
  slave_information = [x for x in loads(partition['slave_instance_list'].encode('utf-8')) if x['slave_title'] == shared_instance['reference']][0]
  # Drop added informations
  slave_information.pop('slave_title')
  slave_information.pop('slap_software_type')
  slave_information.pop('slave_reference')

  return validate_and_send_json_rpc_document({
    "title": title,
    "instance_guid": generateInstanceGuid(title, shared_instance['asked_by'], True),
    "software_release_uri": partition['software_release'],
    "software_type": partition['software_type'],
    # XXX This is not stored
    "state": "started",
    "connection_parameters": xml2dict(shared_instance['connection_xml']),
    "parameters": slave_information,
    "shared": True,
    "root_instance_title": shared_instance['asked_by'] or title,
    "ip_list": [],
    "full_ip_list": [],
    # sla are not stored in slapproxy
    "sla_parameters": {},
    "computer_guid": partition['computer_reference'],
    "compute_partition_id": partition['reference'],
    "processing_timestamp": int(partition['timestamp']),
    # This info is probably not available
    "access_status_message": ''
  })

def send_json_rpc_slap_instance(title, requested_by, is_shared, slap_instance):
  parameters = slap_instance._parameter_dict
  if is_shared:
    # XXX there is not timestamp for shared instance currently
    timestamp = 0
    state = 'started'
  else:
    timestamp = parameters.pop('timestamp')
    state = slap_instance._requested_state
  return validate_and_send_json_rpc_document({
    "title": title,
    "instance_guid": generateInstanceGuid(title, requested_by, is_shared),
    "software_release_uri": slap_instance.slap_software_release_url,
    "software_type": slap_instance.slap_software_type,
    "state": state,
    "connection_parameters": slap_instance._connection_dict,
    "parameters": parameters,
    "shared": is_shared,
    "root_instance_title": requested_by or title,
    "ip_list": [[y for y in x] for x in slap_instance.ip_list],
    "full_ip_list": [],
    # sla are not stored in slapproxy
    "sla_parameters": {},
    "computer_guid": slap_instance.slap_computer_id,
    "compute_partition_id": slap_instance.slap_computer_partition_id,
    "processing_timestamp": int(float(timestamp)),
    # This info is probably not available
    "access_status_message": ''
  })

@json_rpc_blueprint.route('/slapos.get.v0.software_instance', methods=['POST'])
def get_software_instance():
  try:
    partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
  except (ValueError, IndexError):
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])

  if is_shared:
    # XXX Copied from db.getAllocatedSlaveInstance
    shared = execute_db('slave',
      'SELECT * FROM %s WHERE reference=? AND asked_by=?',
      (generateDBSlaveReference(partition_reference, requested_by), requested_by), one=True)
    if not shared:
      return abort(403, 'No shared instance %s found.' % request.json["instance_guid"])
    # Get the matching partition
    partition = execute_db('partition',
      'SELECT * FROM %s WHERE computer_reference=? AND reference=?',
      (shared['computer_reference'], shared['hosted_by']), one=True)
    if not partition:
      return abort(403, 'No partition hosting %s found.' % request.json["instance_guid"])
    return send_json_rpc_sql_shared(shared, partition)

  partition = getAllocatedInstance(partition_reference, requested_by)
  if not partition:
    return abort(403, 'No software instance %s found.' % request.json["instance_guid"])
  return send_json_rpc_sql_partition(partition)

@json_rpc_blueprint.route('/slapos.get.v0.compute_partition', methods=['POST'])
def get_compute_partition():
  partition = getPartitionFromDB(request.json["compute_partition_id"], request.json["computer_guid"])
  if (not partition) or (not partition['partition_reference']):
    return abort(403, 'No instance on partition %s found.' % request.json["compute_partition_id"])
  return send_json_rpc_sql_partition(partition)

@json_rpc_blueprint.route('/slapos.post.v0.software_instance', methods=['POST'])
def post_software_instance():
  title = request.json["title"]
  requested_by = ''# XXX getRequesterFromForm(form) or '',
  parameters = request.json.get("parameters", {})
  is_shared = request.json.get("shared", False)
  requested_state = request.json.get("state", "started")
  parsed_request_dict = {
    'requester_id': None,
    'requested_by': requested_by,
    'software_release': request.json["software_release_uri"],
    'software_type': request.json["software_type"],
    'partition_reference': title,
    'partition_parameter_kw': parameters,
    'filter_kw': request.json.get("sla_parameters", {}),
    # Note: currently ignored for slave instance (slave instances
    # are always started).
    'requested_state': requested_state,
    # Is it a slave instance?
    'slave': is_shared
  }
  try:
    slap_instance = requestInstanceFromDB(**parsed_request_dict)
  except AllocationFailure as e:
    return abort(403, str(e))
  if isinstance(slap_instance, SoftwareInstance):
    return send_json_rpc_slap_instance(title, requested_by, is_shared, slap_instance)

  elif isinstance(slap_instance, ComputerPartition):
    return validate_and_send_json_rpc_document({
      "title": title,
      "instance_guid": generateInstanceGuid(title, requested_by, is_shared),
      "software_release_uri": request.json["software_release_uri"],
      "software_type": request.json["software_type"],
      "state": requested_state,
      "connection_parameters": slap_instance._connection_dict,
      "parameters": parameters,
      "shared": is_shared,
      "root_instance_title": requested_by or title,
      "ip_list": [],
      "full_ip_list": [],
      # sla are not stored in slapproxy
      "sla_parameters": {},
      "computer_guid": slap_instance._computer_id,
      "compute_partition_id": slap_instance._partition_id,
      "processing_timestamp": 0,
      # This info is probably not available
      "access_status_message": ''
    })

  return abort(500, 'Can not export %s' % str(slap_instance))

@json_rpc_blueprint.route('/slapos.put.v0.compute_node_format', methods=['POST'])
def put_compute_node_format():
  formatFromDB(request.json["computer_guid"],
               request.json["compute_partition_list"])
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Formatted'
  })

@json_rpc_blueprint.route('/slapos.put.v0.compute_node_bang', methods=['POST'])
def put_compute_node_bang():
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Ignored'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_installation_reported_state', methods=['POST'])
def put_software_installation_reported_state():
  reported_state = request.json["reported_state"]
  if reported_state in ["available", "building"]:
    return validate_and_send_json_rpc_document({
      'type': 'success',
      'title': 'Ignored'
    })
  elif reported_state == "destroyed":
    removeFromDB(request.json["computer_guid"], request.json["software_release_uri"])
    return validate_and_send_json_rpc_document({
      'type': 'success',
      'title': 'Destroyed'
    })
  else:
    raise NotImplementedError('State %s handling not implemented' % reported_state)

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_reported_state', methods=['POST'])
def put_software_instance_reported_state():
  reported_state = request.json["reported_state"]
  if reported_state in ['started', 'stopped']:
    return validate_and_send_json_rpc_document({
      'type': 'success',
      'title': 'Ignored'
    })

  if reported_state == 'destroyed':
    try:
      partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
    except (ValueError, IndexError):
      return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])

    if is_shared:
      return validate_and_send_json_rpc_document({
        'type': 'success',
        'title': 'Ignored'
      })
    else:

      # Instance is fetched twice from DB
      # Far from optimal, but enough for now, as this is really
      # not called often
      partition = getAllocatedInstance(partition_reference, requested_by)
      if not partition:
        return abort(403, 'No software instance %s found.' % request.json["instance_guid"])

      try:
        freePartitionFromDB(partition['reference'], partition['computer_reference'])
      except (NotFoundPartitionFailure, PartitionDeletionFailure) as error:
        return abort(403, str(error))

      return validate_and_send_json_rpc_document({
        'type': 'success',
        'title': 'Destroyed'
      })

  else:
    raise NotImplementedError('State %s handling not implemented' % reported_state)

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_bang', methods=['POST'])
def put_software_instance_bang():
  try:
    partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
  except (ValueError, IndexError):
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])

  if is_shared:
    return abort(403, 'NotImplemented')
  else:
    bangInstanceFromDB(partition_reference, requested_by)

  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Bang handled'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_title', methods=['POST'])
def put_software_instance_title():
  try:
    partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
  except (ValueError, IndexError):
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])
  new_title = request.json['title']

  if is_shared:
    return abort(403, 'NotImplemented')
    """
    # XXX TODO update slave_instance_list
    query = 'UPDATE %s SET reference=? WHERE reference=? AND asked_by=?'
    argument_list = [
      generateDBSlaveReference(new_title, requested_by),
      generateDBSlaveReference(partition_reference, requested_by),
      requested_by
    ]
    execute_db('slave', query, argument_list)
    """
  else:
    query = 'UPDATE %s SET partition_reference=? WHERE partition_reference=? AND requested_by=?'
    argument_list = [new_title, partition_reference, requested_by]
    execute_db('partition', query, argument_list)

  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Renamed'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_connection_parameter', methods=['POST'])
def put_software_instance_connection_parameter():
  try:
    partition_reference, requested_by, is_shared = extractInstanceGuid(request.json["instance_guid"])
  except (ValueError, IndexError):
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])
  connection_xml = dict2xml(request.json["connection_parameter_dict"])

  if is_shared:
    query = 'UPDATE %s SET connection_xml=? WHERE reference=? AND asked_by=?'
    argument_list = [connection_xml, generateDBSlaveReference(partition_reference, requested_by), requested_by]
    execute_db('slave', query, argument_list)
  else:
    query = 'UPDATE %s SET connection_xml=? WHERE partition_reference=? AND requested_by=?'
    argument_list = [connection_xml, partition_reference, requested_by]
    execute_db('partition', query, argument_list)

  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Updated'
  })


@json_rpc_blueprint.route('/slapos.put.v0.software_instance_error', methods=['POST'])
def put_software_instance_error():
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Ignored'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_installation_error', methods=['POST'])
def put_software_installation_error():
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Ignored'
  })


@json_rpc_experimental_blueprint.route('/slapos.allDocs.WIP.instance_tree_list', methods=['POST'])
def instance_tree_list():
  partition_and_shared_list = getInstanceTreeList()
  result_list = []
  for partition in partition_and_shared_list[0]:
    result_list.append({
      "instance_guid": generateInstanceGuid(partition['partition_reference'], '', False),
      "title": partition['partition_reference']
    })
  for shared in partition_and_shared_list[1]:
    title, asked_by = extractDBSlaveReference(shared['reference'])
    assert asked_by == shared['asked_by']
    result_list.append({
      "instance_guid": generateInstanceGuid(title, '', True),
      "title": title
    })
  return validate_and_send_json_rpc_document({
    'result_list': result_list
  })

@json_rpc_experimental_blueprint.route('/slapos.allDocs.WIP.compute_node_list', methods=['POST'])
def compute_node_list():
  result_list = []
  for computer in execute_db('computer', 'SELECT reference FROM %s', ()):
    result_list.append({
      "computer_guid": computer['reference']
    })
  return validate_and_send_json_rpc_document({
    'result_list': result_list
  })
