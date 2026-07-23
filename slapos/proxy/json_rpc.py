from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.exceptions import NotAcceptable
from flask import current_app, request, abort, Blueprint, make_response, g, url_for
from .db import execute_db, requestInstanceFromDB, supplyFromDB, removeFromDB, \
                formatFromDB, getInstanceByGuid, getInstanceTreeList, \
                getRootInstanceTitle, identifyRequester, renameInstance, \
                bangInstance, setInstanceConnectionParameters, destroyInstance, \
                UnknownRequester, \
                NotFoundPartitionFailure, PartitionDeletionFailure, \
                AllocationFailure, ConfigurationError, HostNotReady, \
                decodeSharedParameters
from slapos.util import xml2dict
from slapos.slap.slap import ComputerPartition
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


def identify_requester_from_headers():
  """Resolve the asserted requester identity once per json_rpc request.

  json_rpc asserts identity through transport metadata (headers), the only
  channel the frozen request schemas leave open. This fails CLOSED: an asserted
  but unresolvable identity aborts 403 before any endpoint body runs, so a bogus
  identity never silently founds a new root tree. Registered AFTER the OpenAPI
  validation hook, so a malformed body still 400s before a bogus identity 403s.
  """
  computer_id = request.headers.get('X-computer-id')
  partition_id = request.headers.get('X-computer-partition-id')
  try:
    g.requester = identifyRequester(computer_id, partition_id)
  except UnknownRequester as e:
    return abort(403, str(e))
  g.requester_id = partition_id or 'user'

json_rpc_blueprint.before_request(identify_requester_from_headers)
json_rpc_experimental_blueprint.before_request(identify_requester_from_headers)


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
    # Legacy slap_tool behavior: the default computer may query before format() registers it.
    if computer_id != current_app.config['computer_id']:
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

@json_rpc_blueprint.route('/slapos.allDocs.v0.compute_node_instance_list', methods=['POST'])
def compute_node_instance_list():
  computer_id = request.json["computer_guid"]
  computer_list = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_id])
  if len(computer_list) != 1:
    # Legacy slap_tool behavior: the default computer may query before format() registers it.
    if computer_id != current_app.config['computer_id']:
      return abort(403, '%s is not registered.' % computer_id)
  # Master lists real Software Instance documents aggregated to the compute node
  # (JSONRPCService_searchComputeNodeSoftwareInstanceFromDict: portal_type
  # "Software Instance", sorted by reference), never the free partition slots. A
  # free slot is not an instance, so it is simply absent -- slapgrid derives free
  # partitions by difference against its local partition set, and a destroyed
  # instance is cleaned while it is still listed with its software_release_uri,
  # before the slot is freed.
  instance_list = []
  for instance in execute_db('instance',
      'SELECT * FROM %s WHERE shared=0 AND allocated_computer=?'
      ' AND allocated_partition IS NOT NULL ORDER BY instance_guid',
      (computer_id,)):
    instance_list.append({
      "title": instance['title'],
      "instance_guid": instance['instance_guid'],
      "state": instance['requested_state'],
      "compute_partition_id": instance['allocated_partition'],
      "software_release_uri": instance['software_release'],
    })
  return validate_and_send_json_rpc_document({
    'result_list': instance_list
  })

@json_rpc_blueprint.route('/slapos.allDocs.v0.instance_node_instance_list', methods=['POST'])
def instance_node_instance_list():
  host = getInstanceByGuid(request.json["instance_guid"])
  if host is None or host['shared'] or host['allocated_partition'] is None:
    return abort(403, 'No software instance %s found.' % request.json["instance_guid"])

  result_list = []
  for row in execute_db('instance',
      'SELECT * FROM %s'
      ' WHERE shared=1 AND allocated_computer=? AND allocated_partition=?'
      ' ORDER BY rowid',
      (host['allocated_computer'], host['allocated_partition'])):
    result_list.append({
      "title": row['title'],
      "instance_guid": row['instance_guid'],
      "software_type": row['software_type'],
      "state": row['requested_state'],
      "parameters": decodeSharedParameters(row['xml']),
      "compute_partition_id": row['allocated_partition']
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

def send_json_rpc_instance(row):
  """Serialize an instance row to the json_rpc software_instance document.

  One serializer for shared and non-shared rows: shared is bool(row['shared']),
  state is the real requested_state, instance_guid is published for both. The
  ip_list comes from the partition_network rows of the (possibly hosting)
  allocated partition."""
  address_list = []
  for address in execute_db('partition_network',
                            'SELECT * FROM %s WHERE partition_reference=? AND computer_reference=?',
                            (row['allocated_partition'], row['allocated_computer'])):
    address_list.append([address['reference'], address['address']])

  return validate_and_send_json_rpc_document({
    "title": row['title'],
    "instance_guid": row['instance_guid'],
    "software_release_uri": row['software_release'],
    "software_type": row['software_type'],
    "state": row['requested_state'],
    "connection_parameters": xml2dict(row['connection_xml']),
    "parameters": decodeSharedParameters(row['xml']) if row['shared']
      else xml2dict(row['xml']),
    "shared": bool(row['shared']),
    "root_instance_title": getRootInstanceTitle(row),
    "ip_list": address_list,
    "full_ip_list": [],
    # sla are not stored in slapproxy
    "sla_parameters": {},
    "computer_guid": row['allocated_computer'],
    "compute_partition_id": row['allocated_partition'],
    "processing_timestamp": int(row['timestamp'] or 0),
    # This info is probably not available
    "access_status_message": ''
  })

@json_rpc_blueprint.route('/slapos.get.v0.software_instance', methods=['POST'])
def get_software_instance():
  row = getInstanceByGuid(request.json["instance_guid"])
  if row is None:
    return abort(403, 'No software instance %s found.' % request.json["instance_guid"])
  return send_json_rpc_instance(row)

@json_rpc_blueprint.route('/slapos.get.v0.compute_partition', methods=['POST'])
def get_compute_partition():
  row = execute_db('instance',
    'SELECT * FROM %s WHERE shared=0 AND allocated_computer=? AND allocated_partition=?',
    (request.json["computer_guid"], request.json["compute_partition_id"]), one=True)
  if row is None:
    return abort(403, 'No instance on partition %s found.' % request.json["compute_partition_id"])
  return send_json_rpc_instance(row)

@json_rpc_blueprint.route('/slapos.post.v0.software_instance', methods=['POST'])
def post_software_instance():
  title = request.json["title"]
  parameters = request.json.get("parameters", {})
  is_shared = request.json.get("shared", False)
  requested_state = request.json.get("state", "started")
  try:
    result = requestInstanceFromDB(
      requester=g.requester,
      requester_id=g.requester_id,
      software_release=request.json["software_release_uri"],
      software_type=request.json["software_type"],
      partition_reference=title,
      partition_parameter_kw=parameters,
      filter_kw=request.json.get("sla_parameters", {}),
      # Note: currently ignored for slave instance (slave instances
      # are always started).
      requested_state=requested_state,
      # Is it a slave instance?
      slave=is_shared)
  except HostNotReady as e:
    # A shared instance whose hosting instance is not available yet. The master
    # keeps the Slave Instance pending and returns the 102 SoftwareInstanceNotReady
    # arm (JSONRPCService_requestSoftwareInstance.py); the host may be allocated
    # on a later slapgrid run, so the client returns a placeholder
    # ComputerPartition and polls (result['status'] == 102 in the json_rpc client).
    return validate_and_send_json_rpc_document({
      'status': 102,
      'name': 'SoftwareInstanceNotReady',
      'message': str(e),
    })
  except AllocationFailure as e:
    # No free partition on this compute node. The proxy allocates synchronously
    # over a fixed partition set with no allocation alarm, so unlike the master
    # (where an unallocatable instance stays pending and returns 102 until an
    # alarm places it) this never resolves on a later poll -- it is terminal.
    # Returning the poll-again 102 arm would make slapgrid retry forever in
    # silence. Surface it as a clear 404 instead, which the json_rpc client maps
    # to NotFoundError, matching the slap_tool blueprint's abort(404, ...).
    return abort(404, str(e))
  except ConfigurationError as e:
    # A misconfigured multimaster forward (external master missing from the
    # multimaster list, or an https master without key/certificate). Surface
    # the explanatory message as a 404, matching the slap_tool blueprint, so
    # the reason is not lost in a generic 500.
    return abort(404, str(e))
  if isinstance(result, ComputerPartition):
    if getattr(result, '_request_dict', None) is not None:
      # The forward reached the external master but the sub-instance is still
      # pending there: the master returned a placeholder ComputerPartition
      # (_request_dict set, no _connection_dict) instead of an allocated one.
      # Dereferencing _connection_dict here would raise -- surface the same 102
      # SoftwareInstanceNotReady arm as the shared host-not-ready path so the
      # client polls, mirroring slap_tool's _request_dict detection (which
      # aborts 408 on the same condition).
      return validate_and_send_json_rpc_document({
        'status': 102,
        'name': 'SoftwareInstanceNotReady',
        'message': 'Software instance %s is not ready' % title,
      })
    # frontend-bypass / external-master forward: no local instance row exists
    return validate_and_send_json_rpc_document({
      "title": title,
      "instance_guid": '%s-%s' % (result._computer_id, result._partition_id),
      "software_release_uri": request.json["software_release_uri"],
      "software_type": request.json["software_type"],
      "state": requested_state,
      "connection_parameters": result._connection_dict,
      "parameters": parameters,
      "shared": is_shared,
      "root_instance_title": getRootInstanceTitle(g.requester)
        if g.requester is not None else title,
      "ip_list": [],
      "full_ip_list": [],
      # sla are not stored in slapproxy
      "sla_parameters": {},
      "computer_guid": result._computer_id,
      "compute_partition_id": result._partition_id,
      "processing_timestamp": 0,
      # This info is probably not available
      "access_status_message": ''
    })
  if result is None:
    # A first-ever shared request with state 'destroyed' allocated nothing.
    return validate_and_send_json_rpc_document({
      'status': 200,
      'name': 'Destroyed',
      'message': 'Shared instance %s destroyed' % title,
    })
  return send_json_rpc_instance(result)

@json_rpc_blueprint.route('/slapos.get.v0.instance_tree', methods=['POST'])
def get_instance_tree():
  root_list = getInstanceTreeList(title=request.json["title"])
  if len(root_list) == 1:
    return send_json_rpc_instance(root_list[0])
  return abort(403, 'No instance tree %s found.' % request.json["title"])

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
      destroyInstance(request.json["instance_guid"])
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
    bangInstance(request.json["instance_guid"])
  except NotFoundPartitionFailure as error:
    return abort(403, str(error))
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Bang handled'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_title', methods=['POST'])
def put_software_instance_title():
  try:
    renameInstance(request.json["instance_guid"], request.json['title'])
  except NotFoundPartitionFailure as error:
    return abort(403, str(error))
  return validate_and_send_json_rpc_document({
    'type': 'success',
    'title': 'Renamed'
  })

@json_rpc_blueprint.route('/slapos.put.v0.software_instance_connection_parameter', methods=['POST'])
def put_software_instance_connection_parameter():
  try:
    setInstanceConnectionParameters(
      request.json["instance_guid"], request.json["connection_parameter_dict"])
  except NotFoundPartitionFailure as error:
    return abort(403, str(error))
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

@json_rpc_blueprint.route('/slapos.allDocs.v0.instance_tree_list', methods=['POST'])
def instance_tree_list():
  result_list = []
  for row in getInstanceTreeList():
    result_list.append({
      "title": row['title']
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
