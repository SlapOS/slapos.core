from flask import Blueprint

henri_blueprint = Blueprint(
  'henri', __name__, static_url_path='', static_folder='static_henri')

@henri_blueprint.route('/', methods=['GET'])
def index():
  return henri_blueprint.send_static_file('index.html')
