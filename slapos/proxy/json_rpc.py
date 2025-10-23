from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import NotAcceptable
from flask import current_app, request, abort, Blueprint, make_response, g
from .db import execute_db
import json
import jsonschema
import sys


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
    return exception


@json_rpc_blueprint.route('/slapos.allDocs.v0.instance_node_instance_list', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.compute_node_status', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.compute_partition', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.hateoas_url', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.software_instance', methods=['POST'])
@json_rpc_blueprint.route('/slapos.get.v0.software_instance_certificate', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.compute_node_certificate', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.compute_node_usage', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.software_installation', methods=['POST'])
@json_rpc_blueprint.route('/slapos.post.v0.software_instance', methods=['POST'])
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
  return '%s___%s' % (partition.reference, partition.computer_reference)

@json_rpc_blueprint.route('/slapos.allDocs.v0.compute_node_instance_list', methods=['POST'])
def compute_node_instance_list():
  computer_id = request.json["computer_guid"]
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    return abort(403, '%s is not registered.' % computer_id)
  instance_list = []
  for partition in execute_db('partition', 'SELECT * FROM %s WHERE computer_reference=?', [computer_id]):
    instance_list.append({
      "title": partition.partition_reference,
      "instance_guid": generateInstanceGuid(partition),
      "state": partition.slap_state,
      "compute_partition_id": partition.reference,
      "software_release_uri": partition.url_string,
    })
  return validate_and_send_json_rpc_document({
    'result_list': instance_list
  })
