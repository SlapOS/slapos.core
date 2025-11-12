from flask import current_app, Blueprint, request, url_for
from werkzeug.exceptions import BadRequest, HTTPException
import requests
from .base64_converter import Base64Converter

#########################################
# Flask Blueprint
#########################################
def register_converter(state):
  state.app.url_map.converters["base64"] = Base64Converter
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


@http_proxy_blueprint.route('/proxy/<base64:url>', methods=['GET'])
def proxy_request(url):
  # Accept-Encoding ? Referer ?
  header_white_list = ["Content-Type", "Accept", "Accept-Language", "Range",
                       "If-Modified-Since", "If-None-Match", "User-Agent"]

  # Fake user access to the document, instead of an ajax query
  if request.headers.get('Sec-Fetch-Dest', 'empty') == 'empty':
    proxy_query_header = {
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
  else:
    header_white_list.append('Sec-Fetch-Dest')
    # Add a fake identical referer if not SecFetchDest == Document
    proxy_query_header = {
        'Sec-Fetch-Mode': 'same-origin',
        'Sec-Fetch-Site': 'same-origin',
    }

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
    raise HTTPSSLError()
  except requests.exceptions.ConnectionError:
    raise HTTPConnectionError()
  except (requests.exceptions.Timeout,
          requests.exceptions.ChunkedEncodingError):
    raise HTTPTimeout()
  except requests.exceptions.TooManyRedirects:
    raise HTTPTooManyRedirect()
#  data=request.stream,
  proxy_response_headers = {
      # If content type is not present, set it to blob/binary
      "Content-Type": "application/octet-stream"
  }
  for k, v in proxy_response.headers.items():
    k = k.title()

    if k in ["Content-Disposition", "Content-Type", "Date", "Last-Modified",
             "Vary", "Cache-Control", "Etag", "Accept-Ranges",
             "Content-Range"]:
      proxy_response_headers[k] = v
    elif k == "Location":
      # In case of redirect, allow to directly fetch from proxy
      proxy_response_headers[k] = url_for('.proxy_request', url=v,
                                          _external=True)

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
