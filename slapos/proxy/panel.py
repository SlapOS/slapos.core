from flask import Blueprint

panel_blueprint = Blueprint('panel', __name__, static_url_path='', static_folder='static_panel')

@panel_blueprint.route('/', methods=['GET'])
def index():
  return panel_blueprint.send_static_file('panel.html')
