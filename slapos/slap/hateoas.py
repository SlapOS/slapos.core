import json
import urlparse
import netaddr
import requests
from uritemplate import expand

from exceptions import NotFoundError, ResourceNotReady, ServerError, \
                       ConnectionError

def _addIpv6Brackets(url): 
  # if master_url contains an ipv6 without bracket, add it 
  # Note that this is mostly to limit specific issues with 
  # backward compatiblity, not to ensure generic detection. 
  api_scheme, api_netloc, api_path, api_query, api_fragment = urlparse.urlsplit(url) 
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
    url = urlparse.urlunsplit((api_scheme, api_netloc, api_path, api_query, api_fragment)) 
  return url 

class ConnectionHelper:
  def __init__(self, master_url, key_file=None,
               cert_file=None, master_ca_file=None, timeout=None):
    master_url = _addIpv6Brackets(master_url)
    if master_url.endswith('/'):
        self.slapgrid_uri = master_url
    else:
        # add a slash or the last path segment will be ignored by urljoin
        self.slapgrid_uri = master_url + '/'
    self.key_file = key_file
    self.cert_file = cert_file
    self.master_ca_file = master_ca_file
    self.timeout = timeout

  def do_request(self, method, path, params=None, data=None, headers=None):
    url = urlparse.urljoin(self.slapgrid_uri, path)
    if headers is None:
      headers = {}
    headers.setdefault('Accept', '*/*')
    if path.startswith('/'):
      path = path[1:]
#      raise ValueError('method path should be relative: %s' % path)

    try:
      if url.startswith('https'):
        cert = (self.cert_file, self.key_file)
      else:
        cert = None

      # XXX TODO: handle host cert verify

      # Old behavior was to pass empty parameters as "None" value.
      # Behavior kept for compatibility with old slapproxies (< v1.3.3).
      # Can be removed when old slapproxies are no longer in use.
      if data:
        for k, v in data.iteritems():
          if v is None:
            data[k] = 'None'

      req = method(url=url,
                   params=params,
                   cert=cert,
                   verify=False,
                   data=data,
                   headers=headers,
                   timeout=self.timeout)
      req.raise_for_status()

    except (requests.Timeout, requests.ConnectionError) as exc:
      raise ConnectionError("Couldn't connect to the server. Please "
                            "double check given master-url argument, and make sure that IPv6 is "
                            "enabled on your machine and that the server is available. The "
                            "original error was:\n%s" % exc)
    except requests.HTTPError as exc:
      if exc.response.status_code == requests.status_codes.codes.not_found:
        msg = url
        if params:
            msg += ' - %s' % params
        raise NotFoundError(msg)
      elif exc.response.status_code == requests.status_codes.codes.request_timeout:
        # this is explicitly returned by SlapOS master, and does not really mean timeout
        raise ResourceNotReady(path)
        # XXX TODO test request timeout and resource not found
      else:
        # we don't know how or don't want to handle these (including Unauthorized)
        req.raise_for_status()
    except requests.exceptions.SSLError as exc:
      raise AuthenticationError("%s\nCouldn't authenticate computer. Please "
                                "check that certificate and key exist and are valid." % exc)

#    XXX TODO parse server messages for client configure and node register
#    elif response.status != httplib.OK:
#      message = parsed_error_message(response.status,
#                                     response.read(),
#                                     path)
#      raise ServerError(message)

    return req

  def GET(self, path, params=None, headers=None):
    req = self.do_request(requests.get,
                          path=path,
                          params=params,
                          headers=headers)
    return req.text.encode('utf-8')

  def POST(self, path, params=None, data=None,
           content_type='application/x-www-form-urlencoded'):
    req = self.do_request(requests.post,
                          path=path,
                          params=params,
                          data=data,
                          headers={'Content-type': content_type})
    return req.text.encode('utf-8')

class HateoasNavigator(object):
  """
  Navigator for HATEOAS-style APIs.
  Inspired by
  https://git.erp5.org/gitweb/jio.git/blob/HEAD:/src/jio.storage/erp5storage.js
  """
  # XXX: needs to be designed for real. For now, just a non-maintainable prototype.
  # XXX: export to a standalone library, independant from slap.
  def __init__(self, slapgrid_uri,
               key_file=None, cert_file=None,
               master_ca_file=None, timeout=60):
    self.slapos_master_hateoas_uri = slapgrid_uri
    self.key_file = key_file
    self.cert_file = cert_file
    self.master_ca_file = master_ca_file
    self.timeout = timeout

  def GET(self, uri, headers=None):
    connection_helper = ConnectionHelper(
        uri, self.key_file, self.cert_file, self.master_ca_file, self.timeout)
    return connection_helper.GET(uri, headers=headers)

  def hateoasGetLinkFromLinks(self, links, title):
    if type(links) == dict:
      if links.get('title') == title:
        return links['href']
      raise NotFoundError('Action %s not found.' % title)
    for action in links:
      if action.get('title') == title:
        return action['href']
    else:
      raise NotFoundError('Action %s not found.' % title)

  def getRelativeUrlFromUrn(self, urn):
    urn_schema = 'urn:jio:get:'
    try:
      _, url = urn.split(urn_schema)
    except ValueError:
      return
    return str(url)

  def getSiteDocument(self, url, headers=None):
    result = self.GET(url, headers)
    return json.loads(result)

  def getRootDocument(self):
    # XXX what about cache?
    cached_root_document = getattr(self, 'root_document', None)
    if cached_root_document:
      return cached_root_document
    self.root_document = self.getSiteDocument(
        self.slapos_master_hateoas_uri,
        headers={'Cache-Control': 'no-cache'}
    )
    return self.root_document

  def getDocumentAndHateoas(self, relative_url, view='view'):
    site_document = self.getRootDocument()
    return expand(
        site_document['_links']['traverse']['href'],
        dict(relative_url=relative_url, view=view)
    )

  def getMeDocument(self):
    person_relative_url = self.getRelativeUrlFromUrn(
        self.getRootDocument()['_links']['me']['href'])
    person_url = self.getDocumentAndHateoas(person_relative_url)
    return json.loads(self.GET(person_url))

class SlapHateoasNavigator(HateoasNavigator):
  def _hateoas_getHostingSubscriptionDict(self):
    action_object_slap_list = self.getMeDocument()['_links']['action_object_slap']
    for action in action_object_slap_list:
      if action.get('title') == 'getHateoasHostingSubscriptionList':
        getter_link = action['href']
        break
    else:
      raise Exception('Hosting subscription not found.')
    result = self.GET(getter_link)
    return json.loads(result)['_links']['content']

  # XXX rename me to blablaUrl(self)
  def _hateoas_getRelatedHostingSubscription(self):
    action_object_slap_list = self.getMeDocument()['_links']['action_object_slap']
    getter_link = self.hateoasGetLinkFromLinks(action_object_slap_list, 
                                               'getHateoasRelatedHostingSubscription')
    result = self.GET(getter_link)
    return json.loads(result)['_links']['action_object_jump']['href']

  def _hateoasGetInformation(self, url):
    result = self.GET(url)
    result = json.loads(result)
    object_link = self.hateoasGetLinkFromLinks(
      result['_links']['action_object_slap'],
      'getHateoasInformation'
    )
    result = self.GET(object_link)
    return json.loads(result)

  def _hateoas_getComputer(self, reference):

    root_document = self.hateoas_navigator.getRootDocument()
    search_url = root_document["_links"]['raw_search']['href']

    getter_link = expand(search_url, {
      "query": "reference:%s AND portal_type:Computer" % reference,
      "select_list": ["relative_url"],
      "limit": 1})

    result = self.GET(getter_link)
    content_list = json.loads(result)['_embedded']['contents']

    if len(content_list) == 0:
      raise Exception('No Computer found.')

    computer_relative_url = content_list[0]["relative_url"]

    getter_url = self.getDocumentAndHateoas(computer_relative_url)

    return json.loads(self.GET(getter_url))

  def getHateoasInstanceList(self, hosting_subscription_url):
    hosting_subscription = json.loads(self.GET(hosting_subscription_url))
    instance_list_url = self.hateoasGetLinkFromLinks(hosting_subscription['_links']['action_object_slap'], 'getHateoasInstanceList')
    instance_list = json.loads(self.GET(instance_list_url))
    return instance_list['_links']['content']

  def getHostingSubscriptionDict(self):
    hosting_subscription_link_list = self._hateoas_getHostingSubscriptionDict()
    hosting_subscription_dict = {}
    for hosting_subscription_link in hosting_subscription_link_list:
      raw_information = self.getHostingSubscriptionRootSoftwareInstanceInformation(hosting_subscription_link['title'])
      software_instance = SoftwareInstance()
      # XXX redefine SoftwareInstance to be more consistent
      for key, value in raw_information.iteritems():
        if key in ['_links']:
          continue
        setattr(software_instance, '_%s' % key, value)
      setattr(software_instance, '_software_release_url', raw_information['_links']['software_release'])
      hosting_subscription_dict[software_instance._title] = software_instance

    return hosting_subscription_dict

  def getHostingSubscriptionRootSoftwareInstanceInformation(self, reference):
    hosting_subscription_list = self._hateoas_getHostingSubscriptionDict()
    for hosting_subscription in hosting_subscription_list:
      if hosting_subscription.get('title') == reference:
        hosting_subscription_url = hosting_subscription['href']
        break
    else:
      raise NotFoundError('This document does not exist.')

    hosting_subscription = json.loads(self.GET(hosting_subscription_url))

    software_instance_url = self.hateoasGetLinkFromLinks(
        hosting_subscription['_links']['action_object_slap'],
        'getHateoasRootInstance'
    )
    response = self.GET(software_instance_url)
    response = json.loads(response)
    software_instance_url = response['_links']['content'][0]['href']
    return self._hateoasGetInformation(software_instance_url)

  def getRelatedInstanceInformation(self, reference):
    related_hosting_subscription_url = self._hateoas_getRelatedHostingSubscription()
    instance_list = self.getHateoasInstanceList(related_hosting_subscription_url)
    instance_url = self.hateoasGetLinkFromLinks(instance_list, reference)
    instance = self._hateoasGetInformation(instance_url)
    return instance


  def getSoftwareInstallationList(self, reference):
    computer = self._hateoas_getComputer(reference)

    # Not a list ?
    action = computer['_links']['action_object_slap']

    if action.get('title') == 'getHateoasSoftwareInstallationList':
      getter_link = action['href']
    else:
      raise Exception('No Link found found.')

    result = self.GET(getter_link)
    return json.loads(result)['_links']['content']

  def getSoftwareInstallationNews(self, url):
    getter_link = None
    for si in self.getSoftwareInstallationList():
      if si["title"] == url:
        getter_link = si["href"]
        break
    
    if getter_link is None:
      return ""
    result = self.GET(getter_link)
    action_object_slap_list = json.loads(result)['_links']['action_object_slap']

    for action in action_object_slap_list:
      if action.get('title') == 'getHateoasNews':
        getter_link = action['href']
        break
    else:
      raise Exception('getHateoasNews not found.')

    result = self.GET(getter_link)
    if len(json.loads(result)['news']) > 0:
      return json.loads(result)['news'][0]["text"]
    return ""

  def getInstanceUrlList(self, name=None, hosting_subscription_url=None):

    if hosting_subscription_url is None:
      hosting_subscription_dict = self._hateoas_getHostingSubscriptionDict()
      for hs in hosting_subscription_dict:
        if hs['title'] == name:
          hosting_subscription_url = hs['href'] 
          break 

    if hosting_subscription_url is None:
      return None

    return self.getHateoasInstanceList(hosting_subscription_url)

  def getNewsFromInstance(self, url):

    result = self.GET(url)
    result = json.loads(result)
    if result['_links'].get('action_object_slap', None) is None:
      return None

    object_link = self.hateoasGetLinkFromLinks(
       result['_links']['action_object_slap'], 'getHateoasNews')
    
    result = self.GET(object_link)
    return json.loads(result)['news']

  def getInformationFromInstance(self, url):

    result = self.GET(url)
    result = json.loads(result)
    if result['_links'].get('action_object_slap', None) is None:
      print result['links']
      return None

    object_link = self.hateoasGetLinkFromLinks(
       result['_links']['action_object_slap'], 'getHateoasInformation')

    return json.loads(self.GET(object_link))
