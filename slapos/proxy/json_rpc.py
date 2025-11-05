from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import NotAcceptable
from flask import current_app, request, abort, Blueprint, make_response, g, url_for
from .db import execute_db
from slapos.util import xml2dict, dict2xml
import json
import jsonschema
import sys
import time


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


def before_request():
  if (request.method != "POST"):
    return abort(405)

  # Validate the input json
  with current_app.open_resource('json_rpc.json', 'r') as json_rpc_open_api_file:
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


json_rpc_blueprint = Blueprint('json_rpc', __name__)
json_rpc_blueprint.before_request(before_request)


class JsonRpcManager(object):
  '''
  This object is used to replicate the slapos master json rpc api
  '''
  def init_app(self, app, **kw):
    app.register_blueprint(json_rpc_blueprint, **kw)
    app.handle_exception = self._custom_handle_exception
    app.handle_http_exception = self._custom_handle_http_exception

  # Redefine http exception handling to return JSON
  def _custom_handle_http_exception(self, exception):
    if request.blueprint == 'json_rpc':
      error_dict = {
        "status": exception.code,
        "type": HTTP_STATUS_CODES.get(exception.code, 'Unknown Error'),
        "title": exception.description
      }
      return send_json_rpc_document(error_dict, status_code=exception.code)
    return exception

  # Redefine python exception handling to return JSON
  def _custom_handle_exception(self, exception):
    if request.blueprint == 'json_rpc':
      # Log exception and return json
      exc_type, exc_value, tb = sys.exc_info()
      current_app.log_exception((exc_type, exc_value, tb))
      return send_json_rpc_document({
        'status': 500,
        'type': HTTP_STATUS_CODES.get(500, 'Unknown Error'),
        'title': 'Internal server error'
      }, status_code=500)
    raise exception


@json_rpc_blueprint.route('/slapos.allDocs.v0.instance_node_instance_list', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.compute_node_status', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.compute_partition', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.software_instance_certificate', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.compute_node_certificate', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.compute_node_usage', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.software_installation', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.compute_node_bang', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.compute_node_format', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_installation_error', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_installation_reported_state', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_instance_bang', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_instance_connection_parameter', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_instance_error', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_instance_reported_state', methods=['POST'])
@json_rpc_blueprint.route('/slapos.put.v0.software_instance_title', methods=['POST'])
@json_rpc_blueprint.route('/slapos.remove.v0.compute_node_certificate', methods=['POST'])
def not_implemented():
  return abort(500, 'Sorry, %s it is not yet implemented in slapproxy' % request.path)

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

def generateInstanceGuid(sql_partition):
  # We expect slapproxy to only a uniq partition_reference/requested_by
  # TODO add a constraint in the SQL table
  return '%s___%s' % (sql_partition['partition_reference'], sql_partition['requested_by'])

def extractInstanceGuid(instance_guid):
  return instance_guid.split('___', 1)

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
      "instance_guid": generateInstanceGuid(partition),
      "state": partition['requested_state'],
      "compute_partition_id": partition['reference'],
      "software_release_uri": partition['software_release'],
    })
  return validate_and_send_json_rpc_document({
    'result_list': instance_list
  })

@json_rpc_blueprint.route('/slapos.get.v0.hateoas_url', methods=['POST'])
def get_hateoas_url():
  return validate_and_send_json_rpc_document({
    'hateoas_url': url_for('hateoas', _external=True)
  })

def send_json_rpc_sql_partition(partition):
  address_list = []
  for address in execute_db('partition_network',
                            'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                            (partition['reference'], partition['computer_reference'])):
    address_list.append([address['reference'], address['address']])

  return validate_and_send_json_rpc_document({
    "title": partition['partition_reference'],
    "instance_guid": generateInstanceGuid(partition),
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
    "processing_timestamp": int(partition['timestamp']),
    # This info is probably not available
    "access_status_message": ''
  })

@json_rpc_blueprint.route('/slapos.get.v0.software_instance', methods=['POST'])
def get_software_instance():
  try:
    partition_reference, requested_by = extractInstanceGuid(request.json["instance_guid"])
  except ValueError:
    return abort(403, 'instance_guid %s not handled.' % request.json["instance_guid"])

  partition = execute_db('partition',
    'SELECT * FROM %s WHERE partition_reference=? AND requested_by=?',
    (partition_reference, requested_by), one=True)
  if not partition:
    return abort(403, 'No software instance %s found.' % request.json["instance_guid"])
  return send_json_rpc_sql_partition(partition)

@json_rpc_blueprint.route('/slapos.post.v0.software_instance', methods=['POST'])
def post_software_instance():
  title = request.json["title"]
  software_release_uri = request.json["software_release_uri"]
  software_type = request.json["software_type"]
  shared = request.json.get("shared", False)
  if shared:
    raise NotImplementedError('shared is not supposed')
  state = request.json.get("state", "started")
  parameters = request.json.get("parameters", {})
  # sla_parameters = request.json.get("sla_parameters", {})

  # TODO
  # - the only supported use case if updating the root instance
  requested_by = ''
  # - factorize the code with views.py
  args = []
  a = args.append
  q = 'UPDATE %s SET slap_state="busy"'

  for k, v in (('requested_state', state),
               ('software_release', software_release_uri),
               ('software_type', software_type),
               ('xml', dict2xml(parameters))):
    # XXX if partition[k] != v:
    q += ', %s=?' % k
    a(v)
    # changed = True

  # - no need to always update the timestamp
  timestamp = time.time()
  q += ', timestamp=?'
  a(timestamp)

  q += ' WHERE partition_reference=? AND requested_by=? AND slap_state=?'
  a(title)
  a('')
  a('busy')

  execute_db('partition', q, args)

  # And send results
  partition = execute_db('partition',
    'SELECT * FROM %s WHERE partition_reference=? AND requested_by=?',
    (title, ''), one=True)
  if not partition:
    return abort(403, 'No partition %s "" found.' % (title))
  return send_json_rpc_sql_partition(partition)
