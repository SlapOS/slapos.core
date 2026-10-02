import subprocess

from flask import Blueprint, jsonify

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
