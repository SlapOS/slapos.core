from lxml import etree
from six.moves.urllib import parse
from six import iteritems, text_type
from slapos.util import bytes2str
import netaddr


def dict2xml(dictionary):
  instance = etree.Element('instance')
  for k, v in iteritems(dictionary):
    if isinstance(k, bytes):
      k = k.decode('utf-8')
    if isinstance(v, bytes):
      v = v.decode('utf-8')
    elif not isinstance(v, text_type):
      v = str(v)
    etree.SubElement(instance, "parameter",
                     attrib={'id': k}).text = v
  return bytes2str(etree.tostring(instance,
                   pretty_print=True,
                   xml_declaration=True,
                   encoding='utf-8'))


def xml2dict(xml):
  result_dict = {}
  if xml is not None and xml != '':
    tree = etree.fromstring(xml.encode('utf-8'))
    for element in tree.findall('parameter'):
      key = element.get('id')
      value = result_dict.get(key, None)
      if value is not None:
        value = value + ' ' + element.text
      else:
        value = element.text
      result_dict[key] = value
  return result_dict


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

