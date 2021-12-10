# -*- coding: utf-8 -*-
# vim: set et sts=2:
##############################################################################
#
# Copyright (c) 2019 Vifib SARL and Contributors.
# All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import json
import six
from six.moves.urllib import parse
from uritemplate import expand
import os
import logging

from ..util import _addIpv6Brackets
from .exception import ResourceNotReady, NotFoundError, \
          AuthenticationError, ConnectionError

import requests
# silence messages like 'Starting connection' that are logged with INFO
urllib3_logger = logging.getLogger('requests.packages.urllib3')
urllib3_logger.setLevel(logging.WARNING)

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

# XXX fallback_logger to be deprecated together with the old CLI entry points.
fallback_logger = logging.getLogger(__name__)
fallback_handler = logging.StreamHandler()
fallback_logger.setLevel(logging.INFO)
fallback_logger.addHandler(fallback_handler)

ALLOWED_JIO_FIELD_LIST = [
  "StringField",
  "EmailField",
  "IntegerField",
  "FloatField",
  "TextAreaField"]

class TempDocument(object):
  def __init__(self, **kw):
    """
    Makes easy initialisation of class parameters
    """
    self.__dict__.update(kw)

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

    # self.session will handle requests using HTTP Cache Control rules.
    self.uncached_session = requests.Session()
    self.session = CacheControl(self.uncached_session,
      cache=FileCache(os.path.expanduser("~/.slapos_cached_get")))

  def do_request(self, method, path, params=None, data=None, headers=None):
    url = parse.urljoin(self.slapgrid_uri, path)
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
        for k, v in six.iteritems(data):
          if v is None:
            data[k] = 'None'

      req = method(url=url,
                   params=params,
                   cert=cert,
                   verify=False,
                   data=data,
                   headers=headers,
                   timeout=self.timeout)
      try:
        req.raise_for_status()
      except TypeError:
        # In Py3, a comparison between NoneType and int can occur if req has no
        # status_code (= None).
        pass

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
    req = self.do_request(self.session.get,
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
    cached_root_document = getattr(self, 'root_document', None)
    if cached_root_document:
      return cached_root_document
    self.root_document = self.getSiteDocument(
        self.slapos_master_hateoas_uri,
        headers={'Cache-Control': 'no-cache'}
    )
    return self.root_document

  def _getSearchUrl(self):
    root_document = self.getRootDocument()
    return root_document["_links"]['raw_search']['href']

  def _getTraverseUrl(self):
    root_document = self.getRootDocument()
    return root_document["_links"]['traverse']['href']

  def _extractPropertyFromFormDict(self, form_dict):
    """ Reimplemenation in python of extractPropertyFromFormJSON of jio.js """
    form = form_dict["_embedded"]["_view"]
    form_data_dict = {}
    converted_dict = {
      "portal_type" : form_dict["_links"]["type"]["name"]
    }

    
    if "parent" in form_dict["_links"]:
      converted_dict["parent_relative_url"] = \
              "/".join(form_dict["_links"]["parent"]["href"].split("/")[-2:])

    form_data_dict["form_id"] = {
      "key": [form["form_id"]["key"]],
      "default": form["form_id"]["default"]
    }

    for key in form:
      field = form[key]
      if key.startswith("my_"):
        key = key[len("my_"):]
      elif key.startswith("your_"):
        key = key[len("your_"):]
      else:
        continue
      
      if field["type"] in ALLOWED_JIO_FIELD_LIST:
        form_data_dict[key] = {
          "default": field.get("default", None),
          "key": field["key"]
        }
        converted_dict[key] = field.get("default", None)

    return {
      "data" : converted_dict,
      "form_data": form_data_dict
    }

  def jio_allDocs(self, query):
    # by default search_url is a Python script (ERP5Document_getHateoas)
    # which enforces a too low limit of what is to be returned (default = 10)
    # as testnode uses this to introspect created ERP5 instance which usually has
    # at least 18 sub instances this limit is too low thus we need to explicitly
    # increase it. 40 is the de-facto default ERP5 preference for number of objects
    # which are usually to be rendered in alistbox 'view' mode
    if 'limit' not in query:
       query['limit'] = 40
    search_url = self._getSearchUrl()
    getter_link = expand(search_url, query)

    catalog_json = self.GET(getter_link)
    catalog_dict = json.loads(catalog_json)

    # Return the same data structure from jio api:
    return {'data': {
        "rows": catalog_dict["_embedded"]["contents"],
        "total_rows": len(catalog_dict["_embedded"]["contents"])
      }
    }

  def jio_get(self, key):
    traverse_url = self._getTraverseUrl()

    # Hardcoded view, but it should come from a site configuration
    view = "slaposjs_view"
    getter_link = expand(traverse_url, {
        "relative_url": key,
        "view": view
        })

    document_json = self.GET(getter_link)
    document_dict = json.loads(document_json)

    return self._extractPropertyFromFormDict(document_dict)

  def jio_getAttachment(self, key, action, options):
    traverse_url = self._getTraverseUrl()

    if action == "view":
      view = "slaposjs_view"
      getter_link = expand(traverse_url, {
        "relative_url": key,
        "view": view
        })
    elif action == "links":
      raise NotImplementedError("links is not implemented for now")
    elif action.startswith(self.slapos_master_hateoas_uri):
      # This is a url, call it directly
      getter_link = action

    document_json = self.GET(getter_link)
    document_dict = json.loads(document_json)

    return document_dict

  def _getMeUrl(self):
    return self.getRelativeUrlFromUrn(
        self.getRootDocument()['_links']['me']['href'])

  def getMeDocument(self):
    # User can be a Person, Software Instance or Computer
    return self.jio_get(self._getMeUrl())

class SlapHateoasNavigator(HateoasNavigator):

  ###############################################################
  # API for Client as a Person
  ###############################################################
  def _getInstanceTreeList(self, title=None, select_list=["title", "url_string"]):
    query_str = 'portal_type:"Instance Tree" AND validation_state:validated'
    if title is not None:
      query_str = 'portal_type:"Instance Tree" AND validation_state:validated AND title:="%s"' % title

    result = self.jio_allDocs(
      query={"query" : query_str, "select_list": select_list})

    return result['data']['rows']

  def _getComputerList(self, title=None, reference=None, select_list=["title", "reference"]):
    query_str = 'portal_type:"Computer" AND validation_state:validated'
    if title is not None:
      query_str += ' AND title:="%s"' % title

    if reference is not None:
      query_str += ' AND reference:="%s"' % reference

    result = self.jio_allDocs(
      query={"query" : query_str, "select_list": select_list})

    return result['data']['rows']

  def getInstanceTreeInstanceList(self, title):
    select_list = ['uid', 'title', 'relative_url', 'portal_type', 
            'url_string', 'text_content', 'getConnectionXmlAsDict',
            'SoftwareInstance_getNewsDict']
    query_str = 'portal_type:("Software Instance", "Slave Instance") AND validation_state:validated'
    query_str += ' AND default_specialise_title:="%s"' % title
    result = self.jio_allDocs(
      query={"query" : query_str, "select_list": select_list})

    return result['data']['rows']

  def getInstanceTreeDict(self, title=None):
    instance_tree_list = self._getInstanceTreeList(title=title)
    instance_tree_dict = {}
    for instance_tree in instance_tree_list:
      software_instance = TempDocument()
      for key, value in six.iteritems(instance_tree):
        if key in ['_links', 'url_string']:
          continue
        setattr(software_instance, '_%s' % key, value)
      setattr(software_instance, '_software_release_url', instance_tree["url_string"])
      instance_tree_dict[software_instance._title] = software_instance

    return instance_tree_dict

  def getComputerDict(self):
    computer_list = self._getComputerList()
    computer_dict = {}
    for computer_json  in computer_list:
      computer = TempDocument()
      for key, value in six.iteritems(computer_json):
        if key in ['_links']:
          continue
        setattr(computer, '_%s' % key, value)
      computer_dict[computer._title] = computer

    return computer_dict

  def getToken(self):
    root_document = self.getRootDocument()
    hateoas_url = root_document['_links']['self']['href']
    token_json = self.jio_getAttachment(
      "computer_module", hateoas_url +  "/computer_module/Base_getComputerToken", {})

    return token_json["access_token"]

  def getInstanceTreeRootSoftwareInstanceInformation(self, reference):
    instance_tree_list = self._getInstanceTreeList(title=reference,
      select_list=["title", "relative_url"])

    assert len(instance_tree_list) <= 1, \
      "There are more them one Instance Tree for this reference"

    instance_tree_jio_key = None
    for instance_tree_candidate in instance_tree_list:
      if instance_tree_candidate.get('title') == reference:
        instance_tree_jio_key = instance_tree_candidate['relative_url']
        break

    if instance_tree_jio_key is None:
      raise NotFoundError('This document does not exist.')

    return self.jio_get(instance_tree_jio_key)

  def _getComputer(self, reference):
    computer_list = self._getComputerList(reference=reference,
      select_list=["reference", "relative_url"])

    assert len(computer_list) <= 1, \
      "There are more them one Computer for this reference"

    computer_jio_key = None
    for computer_candidate in computer_list:
      if computer_candidate.get("reference") == reference:
        computer_jio_key = computer_candidate['relative_url']
        break

    if computer_jio_key is None:
      raise NotFoundError('This computer does not exist.')

    return self.jio_get(computer_jio_key)

  def getSoftwareInstallationList(self, computer_guid=None,
          select_list=['uid', 'relative_url', 'url_string', 'SoftwareInstallation_getNewsDict']):
    query_str = 'portal_type:"Software Installation" AND validation_state:validated'
    if computer_guid is not None:
      query_str += ' AND default_aggregate_reference:="%s"' % computer_guid

    result = self.jio_allDocs(
      query={"query" : query_str, "select_list": select_list})

    return result['data']['rows']

  def getInstanceNews(self, url):
    return self.jio_get(url)['news']

  def getSoftwareInstallationNews(self, computer_guid=None, url=None):
    for si in self.getSoftwareInstallationList(computer_guid):
      if si["url_string"] == url:
        return si['SoftwareInstallation_getNewsDict']['text']
    return "#error no data found"

  def getComputerNews(self, computer_guid):
    return self._getComputer(reference=computer_guid)['data']['news']['computer']['text']

  def getComputerPartitionNews(self, computer_guid, partition_id):
    try:
      return self._getComputer(reference=computer_guid)['data']['news']['partition'][partition_id]['text']
    except KeyError:
      return "#error no data found"


