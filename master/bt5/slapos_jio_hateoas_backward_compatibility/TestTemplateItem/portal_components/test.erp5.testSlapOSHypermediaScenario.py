# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

import json
import httplib
import urlparse
import base64
from unittest import skip

def hateoasGetLinkFromLinks(links, title):
  if type(links) == dict:
    if links.get('title') == title:
      return links
    return
  for action in links:
    if action.get('title') == title:
      return action

def getRelativeUrlFromUrn(urn):
  urn_schema = 'urn:jio:get:'
  try:
    _, url = urn.split(urn_schema)
  except ValueError:
    return
  return url

class TestSlapOSHypermediaPersonScenario(SlapOSTestCaseMixin):

  def _makeUser(self):
    person_user = self.makePerson()
    login = person_user.objectValues("ERP5 Login")[0]
    login.edit(
      reference=person_user.getReference(),
      password=person_user.getReference())
    self.tic()
    return person_user

  @skip("Hypermedia is not supported anymore.")
  def test(self):
    erp5_person = self._makeUser()
    self.tic()
    self.portal.changeSkin('Hal')
    self.tic()

    authorization = 'Basic %s' % base64.b64encode(
      "%s:%s" % (erp5_person.getReference(), erp5_person.getReference()))
    content_type = "application/hal+json"

    api_scheme, api_netloc, api_path, api_query, \
        api_fragment = urlparse.urlsplit(self.portal.absolute_url())

    def getNewHttpConnection(api_netloc):
      if api_scheme == 'https':
        raise Exception('Please connect directly to the Zope server')
      connection = httplib.HTTPConnection(api_netloc)
      return connection

    #####################################################
    # Access the master home page hal
    #####################################################

    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method='GET',
      url='%s/web_site_module/hateoas/' % \
          self.portal.absolute_url(),
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    home_page_hal = json.loads(response.read())

    #####################################################
    # Fetch the user hal
    #####################################################

    user_link_dict = home_page_hal['_links']['me']
    self.assertNotEqual(user_link_dict, None)

    traverse_url_template = home_page_hal['_links']['traverse']['href']
    me_relative_url = getRelativeUrlFromUrn(user_link_dict['href'])
    me_url = traverse_url_template.replace(
        '{&relative_url,view}',
        '&relative_url=%s&view=view' % me_relative_url
    )

    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=me_url,
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    user_hal = json.loads(response.read())

    #####################################################
    # Run method to request an instance tree
    #####################################################

    request_link_dict = hateoasGetLinkFromLinks(
        user_hal['_links']['action_object_slap_post'],
        'requestHateoasInstanceTree'
    )
    self.assertNotEqual(request_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=request_link_dict.get('method', 'POST'),
      url=request_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Content-Type': 'application/json',
      },
      body=json.dumps({
        'software_release': 'http://example.orgé',
        'title': 'a great titleé',
        'software_type': 'fooé',
        'parameter': {'param1é': 'value1é', 'param2é': 'value2é'},
        'sla': {'param3é': 'value3é', 'param4é': 'value4é'},
        'slave': False,
        'status': 'started',
      }),
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 201)

    self.tic()

    #####################################################
    # Get user's instance tree list
    #####################################################
    user_link_dict = hateoasGetLinkFromLinks(
        user_hal['_links']['action_object_slap'],
        'getHateoasInstanceTreeList'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    subscription_collection_hal = json.loads(response.read())

    #####################################################
    # Get user's instance tree
    #####################################################
    subscription_link_dict = subscription_collection_hal['_links']\
        ['content'][0]
    self.assertNotEqual(subscription_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=subscription_link_dict.get('method', 'GET'),
      url=subscription_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    subscription_hal = json.loads(response.read())

    #####################################################
    # Get instance tree's instance list
    #####################################################
    user_link_dict = hateoasGetLinkFromLinks(
        subscription_hal['_links']['action_object_slap'],
        'getHateoasInstanceList'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    instance_collection_hal = json.loads(response.read())

    #####################################################
    # Get instance
    #####################################################
    subscription_link_dict = instance_collection_hal['_links']\
        ['content'][0]
    self.assertNotEqual(subscription_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=subscription_link_dict.get('method', 'GET'),
      url=subscription_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    instance_hal = json.loads(response.read())

    #####################################################
    # Fetch instance informations
    #####################################################

    request_link_dict = hateoasGetLinkFromLinks(
        instance_hal['_links']['action_object_slap'],
        'getHateoasInformation'
    )
    self.assertNotEqual(request_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=request_link_dict.get('method', 'GET'),
      url=request_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)

    self.tic()

    #####################################################
    # Get instance news
    #####################################################
    news_link_dict = hateoasGetLinkFromLinks(
        instance_hal['_links']['action_object_slap'],
        'getHateoasNews'
    )
    self.assertNotEqual(news_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=news_link_dict.get('method', 'GET'),
      url=news_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    news_hal = json.loads(response.read())

    # We are going to check compute_node and software
    # First create a compute_node and a software. We could alternatively later
    # create them through hypermedia links
    self.login(erp5_person.getUserId())
    self.portal.portal_slap.requestComputer(
                       "compute node %s" % erp5_person.getReference())
    self.tic()
    compute_node = self.portal.portal_catalog(portal_type="Compute Node",
                   sort_on=[('creation_date','descending')])[0].getObject()
    self.tic()
    self.portal.portal_slap.supplySupply("http://foo.com/software.cfg",
                                         compute_node.getReference(), "available")
    self.tic()
    self.logout()

    #####################################################
    # Get user's compute_node list
    #####################################################
    user_link_dict = hateoasGetLinkFromLinks(
        user_hal['_links']['action_object_slap'],
        'getHateoasComputeNodeList'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    compute_node_collection_hal = json.loads(response.read())

    #####################################################
    # Get user's compute_node
    #####################################################
    compute_node_link_dict = compute_node_collection_hal['_links']\
        ['content'][0]
    self.assertNotEqual(compute_node_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=compute_node_link_dict.get('method', 'GET'),
      url=compute_node_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    compute_node_hal = json.loads(response.read())

    #####################################################
    # Get compute_node's software list
    #####################################################
    compute_node_link_dict = hateoasGetLinkFromLinks(
        compute_node_hal['_links']['action_object_slap'],
        'getHateoasSoftwareInstallationList'
    )
    self.assertNotEqual(compute_node_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=compute_node_link_dict.get('method', 'GET'),
      url=compute_node_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    software_collection_hal = json.loads(response.read())

    #####################################################
    # Get user's software
    #####################################################
    software_link_dict = software_collection_hal['_links']\
        ['content'][0]
    self.assertNotEqual(software_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=software_link_dict.get('method', 'GET'),
      url=software_link_dict['href'],
      headers={
       'Authorization': authorization,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
    self.assertEqual(response.getheader('Content-Type'), content_type)
    software_hal = json.loads(response.read())


class TestSlapOSHypermediaInstanceScenario(SlapOSTestCaseMixin):

  def generateNewId(self):
    return "%shype" % self.portal.portal_ids.generateNewId(
        id_group=('slapos_core_test'))

  def generateNewSoftwareReleaseUrl(self):
    return 'http://example.org/test%s.cfg' % self.generateNewId()

  def generateNewSoftwareType(self):
    return 'Type %s' % self.generateNewId()

  def generateNewSoftwareTitle(self):
    return 'Title %s' % self.generateNewId()

  @skip("Hypermedia is not supported anymore.")
  def test(self):
    self._makeTree()
    instance = self.software_instance

    self._addERP5Login(self.software_instance)

    self.portal.changeSkin('Hal')
    self.tic()

    remote_user = instance.getUserId()
    content_type = "application/hal+json"

    api_scheme, api_netloc, api_path, api_query, \
        api_fragment = urlparse.urlsplit(self.portal.absolute_url())

    def getNewHttpConnection(api_netloc):
      if api_scheme == 'https':
        raise Exception('Please connect directly to the Zope server')
      connection = httplib.HTTPConnection(api_netloc)
      return connection

    #####################################################
    # Access the master home page hal
    #####################################################

    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method='GET',
      url='%s/web_site_module/hateoas/' % \
          self.portal.absolute_url(),
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
    self.assertEqual(response.status, 200, response)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    home_page_hal = json.loads(response.read())

    #####################################################
    # Fetch the instance hal
    #####################################################

    user_link_dict = home_page_hal['_links']['me']
    self.assertNotEqual(user_link_dict, None)

    traverse_url_template = home_page_hal['_links']['traverse']['href']
    me_relative_url = getRelativeUrlFromUrn(user_link_dict['href'])
    me_url = traverse_url_template.replace(
        '{&relative_url,view}',
        '&relative_url=%s&view=view' % me_relative_url
    )

    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=me_url,
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    instance_hal = json.loads(response.read())

    #####################################################
    # Fetch instance informations
    #####################################################

    user_link_dict = hateoasGetLinkFromLinks(
        instance_hal['_links']['action_object_slap'],
        'getHateoasInformation'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()

    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)

    self.tic()

    #####################################################
    # Get instance news
    #####################################################
    user_link_dict = hateoasGetLinkFromLinks(
        instance_hal['_links']['action_object_slap'],
        'getHateoasNews'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)

    self.tic()

    #####################################################
    # Get instance tree of instance
    #####################################################
    # XXX can be simpler and doesn't need getHateoasRelatedInstanceTree script
    hosting_link_dict = hateoasGetLinkFromLinks(
        instance_hal['_links']['action_object_slap'],
        'getHateoasRelatedInstanceTree'
    )
    self.assertNotEqual(hosting_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=hosting_link_dict.get('method', 'GET'),
      url=hosting_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    subscription_hal = json.loads(response.read())

    self.tic()


    hosting_link_dict = hateoasGetLinkFromLinks(
        subscription_hal['_links']['action_object_jump'],
        'Instance Tree'
    )
    self.assertNotEqual(hosting_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=hosting_link_dict.get('method', 'GET'),
      url=hosting_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()
 
    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    subscription_hal = json.loads(response.read())

    self.tic()

    #####################################################
    # Get instance tree's instance list
    #####################################################
    user_link_dict = hateoasGetLinkFromLinks(
        subscription_hal['_links']['action_object_slap'],
        'getHateoasInstanceList'
    )
    self.assertNotEqual(user_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=user_link_dict.get('method', 'GET'),
      url=user_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()

    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    instance_collection_hal = json.loads(response.read())

    #####################################################
    # Get instance
    #####################################################
    subscription_link_dict = instance_collection_hal['_links']\
        ['content'][0]
    self.assertNotEqual(subscription_link_dict, None)
    connection = getNewHttpConnection(api_netloc)
    connection.request(
      method=subscription_link_dict.get('method', 'GET'),
      url=subscription_link_dict['href'],
      headers={
       'REMOTE_USER': remote_user,
       'Accept': content_type,
      },
      body="",
    )
    response = connection.getresponse()

    self.assertEqual(response.status, 200)
    self.assertEqual(response.getheader('Content-Type'), content_type)
    instance_hal = json.loads(response.read())
