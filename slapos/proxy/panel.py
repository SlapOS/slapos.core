from flask import Blueprint, abort, send_from_directory, current_app

panel_blueprint = Blueprint('panel', __name__, static_url_path='', static_folder='static_panel')

@panel_blueprint.route('/', methods=['GET'])
def index():
  return panel_blueprint.send_static_file('panel.html')

@panel_blueprint.route('/public/<path:filename>')
def download_public_file(filename):
  config_parameter_key = 'PUBLIC_DIRECTORY_PATH'
  if config_parameter_key in current_app.config:
    return send_from_directory(
      current_app.config[config_parameter_key],
      filename,
      # As the content of the public directory is unknown,
      # prevent publishing any kind of website from the proxy
      as_attachment=True,
      # handle 304 status
      conditional=True
    )
  else:
    # 404 is not used, to help understanding that the
    # panel is not configured to search the public directory
    return abort(403, 'The public directory path is not configured.')
