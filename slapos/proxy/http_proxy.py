from flask import current_app, Blueprint, request, url_for
from werkzeug.exceptions import BadRequest, HTTPException
import requests
from six.moves.urllib.parse import urlparse
from .absolute_path_converter import AbsolutePathConverter

#########################################
# Flask Blueprint
#########################################
def register_converter(state):
  state.app.url_map.converters["absolute_path"] = AbsolutePathConverter
http_proxy_blueprint = Blueprint('httpproxy', __name__)
http_proxy_blueprint.record_once(register_converter)


class HTTPSSLError(HTTPException):
  code = 526
  description = 'Invalid SSL Certificate'


class HTTPConnectionError(HTTPException):
  code = 523
  description = 'Connection Error'


class HTTPTimeout(HTTPException):
  code = 524
  description = 'Connection Timeout'


class HTTPTooManyRedirect(HTTPException):
  code = 520
  description = 'Too Many Redirects'


@http_proxy_blueprint.route('/<url_scheme>/<url_netloc>', methods=['HEAD', 'GET', 'OPTIONS'])
@http_proxy_blueprint.route('/<url_scheme>/<url_netloc><absolute_path:url_path>', methods=['HEAD', 'GET', 'OPTIONS'])
def proxy_request(url_scheme, url_netloc, url_path=''):
  url = urlparse('')._replace(
    scheme=url_scheme,
    netloc=url_netloc,
    path=url_path,
    query=request.query_string.decode()
  ).geturl()
  # Accept-Encoding ? Referer ?
  header_white_list = ["Content-Type", "Accept", "Accept-Language", "Range",
                       "If-Modified-Since", "If-None-Match", "User-Agent",
                       # Authorization is required for the stack private stack monitor
                       "Authorization",
                       # Allow CORS
                       "Origin"]

  proxy_query_header = {}
  for k, v in dict(request.headers).items():
    if k in header_white_list:
      proxy_query_header[k] = v

  try:
    proxy_response = requests.request(
        request.method,
        url,
        # ignore verifying the SSL certificate
        # as most backend servers uses self signed certificates
        verify=False,
        data=request.get_data(),
        headers=proxy_query_header,
        timeout=5
    )
  except requests.exceptions.InvalidSchema:
    raise BadRequest('"url" must be http')
  except requests.exceptions.SSLError:
    raise HTTPSSLError(url)
  except requests.exceptions.ConnectionError:
    raise HTTPConnectionError(url)
  except (requests.exceptions.Timeout,
          requests.exceptions.ChunkedEncodingError):
    raise HTTPTimeout(url)
  except requests.exceptions.TooManyRedirects:
    raise HTTPTooManyRedirect(url)
#  data=request.stream,
  proxy_response_headers = {
      # If content type is not present, set it to blob/binary
      "Content-Type": "application/octet-stream"
  }
  for k, v in proxy_response.headers.items():
    k = k.title()

    if k in ["Content-Type", "Date", "Last-Modified",
             "Vary", "Cache-Control", "Etag", "Accept-Ranges",
             "Content-Range",
             # Authorization is required for the stack private stack monitor 
             "Www-Authenticate",
             # Allow CORS
             "Access-Control-Allow-Origin",
             "Access-Control-Allow-Methods",
             "Access-Control-Expose-Headers",
             "Access-Control-Allow-Headers",
             "Access-Control-Allow-Credentials",
             ]:
      proxy_response_headers[k] = v
    elif k == "Location":
      parsed_v = urlparse(v)
      # In case of redirect, allow to directly fetch from proxy
      proxy_response_headers[k] = url_for('.proxy_request',
                                          url_scheme=parsed_v.scheme,
                                          url_netloc=parsed_v.netloc,
                                          url_path=parsed_v.path,
                                          _external=True)
      if parsed_v.query:
        proxy_response_headers[k] += '?%s' % parsed_v.query

  # XSS protection
  # Prevent browser to display untrusted HTML
  proxy_response_headers['Content-Disposition'] = 'attachment'

  status_code = proxy_response.status_code
  if status_code == 500:
    status_code = 520
  return current_app.response_class(
      proxy_response.content,
      status=status_code,
      headers=proxy_response_headers
  )
