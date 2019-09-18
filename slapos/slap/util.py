from six.moves.urllib import parse
import netaddr


def _addIpv6Brackets(url):
  # if master_url contains an ipv6 without bracket, add it
  # Note that this is mostly to limit specific issues with
  # backward compatiblity, not to ensure generic detection.
  api_scheme, api_netloc, api_path, api_query, api_fragment = parse.urlsplit(url)
  try:
    ip = netaddr.IPAddress(api_netloc)
    port = None
  except netaddr.AddrFormatError:
    try:
      ip = netaddr.IPAddress(':'.join(api_netloc.split(':')[:-1]))
      port = api_netloc.split(':')[-1]
    except netaddr.AddrFormatError:
      ip = port = None
  if ip and ip.version == 6:
    api_netloc = '[%s]' % ip
    if port:
      api_netloc = '%s:%s' % (api_netloc, port)
    url = parse.urlunsplit((api_scheme, api_netloc, api_path, api_query, api_fragment))
  return url

