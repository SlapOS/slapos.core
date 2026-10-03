import json
import os
import subprocess
import tempfile

from flask import Blueprint, abort, jsonify, request

henri_blueprint = Blueprint(
  'henri', __name__, static_url_path='', static_folder='static_henri')

@henri_blueprint.route('/', methods=['GET'])
def index():
  return henri_blueprint.send_static_file('index.html')

def capture_ip_route(family):
  """Run ``ip -4 route`` or ``ip -6 route`` and return stdout. Empty on failure."""
  process = subprocess.Popen(
    ['ip', family, 'route'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    universal_newlines=True,
  )
  try:
    stdout, _stderr = process.communicate(timeout=5)
  except subprocess.TimeoutExpired:
    process.kill()
    process.communicate()
    return ''
  if process.returncode != 0:
    return ''
  return stdout or ''

@henri_blueprint.route('/os-routes', methods=['GET'])
def os_routes():
  """Live host routing table. Called by the Henri UI whenever the screen asks."""
  try:
    payload = {
      'ipv4': capture_ip_route('-4'),
      'ipv6': capture_ip_route('-6'),
    }
  except OSError:
    payload = {
      'ipv4': '',
      'ipv6': '',
      'error': 'The ip command is not available on this machine.',
    }
  return jsonify(payload)

def production_set_path():
  """Station data, next to the running partition, not inside the software release."""
  directory = os.environ.get("HENRI_DATA_DIR")
  if not directory:
    directory = os.path.join(os.getcwd(), "var", "henri")
  if not os.path.isdir(directory):
    os.makedirs(directory)
  return os.path.join(directory, "production-set.json")

def read_production_set():
  path = production_set_path()
  if not os.path.exists(path):
    return {}
  with open(path, "r") as handle:
    data = json.load(handle)
  if not isinstance(data, dict):
    return {}
  return data

def sanitize_production_set(payload):
  if not isinstance(payload, dict):
    abort(400)
  cleaned = {}
  for key, value in payload.items():
    if not isinstance(key, str) or not key or len(key) > 200:
      continue
    if any(character in key for character in "/\\\0"):
      continue
    if not isinstance(value, dict):
      continue
    item = {}
    label = value.get("label")
    icon = value.get("icon")
    if isinstance(label, str) and label:
      item["label"] = label[:80]
    if isinstance(icon, str) and icon:
      item["icon"] = icon[:8]
    for coord in ("x", "y"):
      number = value.get(coord)
      if isinstance(number, (int, float)) and not isinstance(number, bool):
        item[coord] = number
    if item:
      cleaned[key] = item
  return cleaned

def write_production_set(data):
  path = production_set_path()
  directory = os.path.dirname(path)
  fd, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
  try:
    with os.fdopen(fd, "w") as handle:
      json.dump(data, handle)
    os.replace(temp_path, path)
  except Exception:
    if os.path.exists(temp_path):
      os.remove(temp_path)
    raise

@henri_blueprint.route('/production-set', methods=['GET'])
def get_production_set():
  """Labels, icons and canvas positions for the Production Set screen."""
  try:
    return jsonify(read_production_set())
  except (OSError, ValueError):
    return jsonify({})

@henri_blueprint.route('/production-set', methods=['PUT'])
def put_production_set():
  """Replace the Production Set document. The body is the full object."""
  data = sanitize_production_set(request.get_json(force=True, silent=True))
  try:
    write_production_set(data)
  except OSError:
    abort(500)
  return jsonify(data)
