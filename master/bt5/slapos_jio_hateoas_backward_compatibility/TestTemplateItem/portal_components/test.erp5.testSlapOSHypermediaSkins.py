# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, changeSkin, simulate
from erp5.component.test.testHalJsonStyle import \
  do_fake_request

import json
from zExceptions import Unauthorized

class TestSlapOSHypermediaMixin(SlapOSTestCaseMixinWithAbort):
  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    self.changeSkin('Hal')

  def _makePerson(self):
    person_user = self.makePerson()
    self.tic()
    self.changeSkin('Hal')
    return person_user

  def _makeInstanceTree(self):
    instance_tree = self.portal.instance_tree_module\
        .template_instance_tree.Base_createCloneDocument(batch_mode=1)
    instance_tree.validate()
    self.tic()
    self.changeSkin('Hal')
    return instance_tree

  def _makeInstance(self):
    instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    instance.validate()
    self.tic()
    return instance

  def _makeComputeNode(self):
    compute_node = self.portal.compute_node_module\
        .template_compute_node.Base_createCloneDocument(batch_mode=1)
    compute_node.validate()
    self.tic()
    return compute_node

  def _makeSoftwareInstallation(self):
    software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    software_installation.validate()
    self.tic()
    return software_installation

class TestSlapOSPersonERP5Document_getHateoas(TestSlapOSHypermediaMixin):

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasPerson_wrong_ACCEPT(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("GET")
    result = person_user.ERP5Document_getHateoas(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasPerson_bad_method(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("POST")
    result = person_user.ERP5Document_getHateoas(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")


  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasPerson_result(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("GET")
    result = person_user.ERP5Document_getHateoas(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    results = json.loads(result)
    action_object_slap = results['_links']['action_object_slap']
    self.assertEqual(len(action_object_slap), 3)
    for action in [
      {
        u'href': u'%s/Person_getHateoasComputeNodeList' % \
          person_user.absolute_url(),
        u'name': u'get_hateoas_compute_node_list',
        u'icon': u'',
        u'title': u'getHateoasComputeNodeList'
      },
      {
        u'href': u'%s/Person_getHateoasInstanceTreeList' % \
          person_user.absolute_url(),
        u'name': u'get_hateoas_instance_tree_list',
        u'icon': u'',
        u'title': u'getHateoasInstanceTreeList'
      },
      {
        u'href': u'%s/Person_getHateoasInformation' % \
          person_user.absolute_url(),
        u'name': u'get_hateoas_information',
        u'icon': u'',
        u'title': u'getHateoasInformation'
      },
    ]:
      self.assertTrue(action in action_object_slap, \
        "%s not in %s" % (action, action_object_slap))
    self.assertEqual(results['_links']['action_object_slap_post'], {
        u"href": u'%s/Person_requestHateoasInstanceTree' %  \
          person_user.absolute_url(),
        u"name": u"request_hateoas_instance_tree",
        u'icon': u'',
        u"title": u"requestHateoasInstanceTree"
    })



class TestSlapOSERP5Document_getHateoas_me(TestSlapOSHypermediaMixin):
  """
    Complementary tests to ensure "me" is present on the request.
  """

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def _test_me(self, me=None):
    self.changeSkin('Hal')
    fake_request = do_fake_request("GET")
    result = self.portal.ERP5Document_getHateoas(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    result = json.loads(result)
    self.assertEqual(result['_links']['self'],
        {"href": "http://example.org/bar"}
    )
    self.assertEqual(result['_links'].get('me'), me)

  def test_me_annonymous(self):
    self.logout()
    self._test_me()

  def test_me_person(self):
    person_user = self._makePerson()
    self.login(person_user.getUserId())
    self._test_me(
      {"href": "urn:jio:get:%s" % person_user.getRelativeUrl()})

  def test_me_instance(self):
    self._makeTree()
    self.login(self.software_instance.getUserId())
    self._test_me(
      {"href": "urn:jio:get:%s" % self.software_instance.getRelativeUrl()}
    )

  def test_me_compute_node(self):
    compute_node = self._makeComputeNode()
    self.tic()
    self.login(compute_node.getUserId())
    self._test_me(
      {"href": "urn:jio:get:%s" % compute_node.getRelativeUrl()}
    )

class TestSlapOSPerson_requestHateoasInstanceTree(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Person_requestHateoasInstanceTree
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_wrong_CONTENT(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("POST")
    result = person_user.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/json"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_bad_method(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("GET")
    result = person_user.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/json"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_not_person_context(self):
    fake_request = do_fake_request("POST")
    result = self.portal.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestBody', '*args, **kwargs',
            'return "[}"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/json"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_no_json(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("POST")
    result = person_user.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 400)
    self.assertEqual(result, "")

  @simulate('Base_getRequestBody', '*args, **kwargs',
            'return "%s"' % json.dumps({
              }))
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/json"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_missing_parameter(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("POST")
    result = person_user.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 400)
    self.assertEqual(result, "")

  @simulate('Base_getRequestBody', '*args, **kwargs',
            'return """%s"""' % json.dumps({
  'software_release': 'http://example.orgé',
  'title': 'a great titleé',
  'software_type': 'fooé',
  'parameter': {'param1é': 'value1é', 'param2é': 'value2é'},
  'sla': {'param3': 'value3é', 'param4é': 'value4é'},
  'slave': False,
  'status': 'started',
              }))
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/json"')
  @changeSkin('Hal')
  def test_requestHateoasInstanceTree_result(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("POST")
    result = person_user.Person_requestHateoasInstanceTree(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 201)
    self.assertEqual(result, "")
    # XXX Test that person.request is called.

class TestSlapOSPerson_getHateoasInstanceTreeList(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_getHateoasInstanceTreeList_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Person_getHateoasInstanceTreeList
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasInstanceTreeList_wrong_ACCEPT(self):
    person_user = self._makePerson()
    fake_request = do_fake_request("GET")
    result = person_user.Person_getHateoasInstanceTreeList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json')
  @changeSkin('Hal')
  def test_getHateoasInstanceTreeList_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.Person_getHateoasInstanceTreeList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasInstanceTreeList_not_person_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Person_getHateoasInstanceTreeList(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/foo"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  def test_getHateoasInstanceTreeList_person_result(self):
    person_user = self._makePerson()
    instance_tree = self._makeInstanceTree()
    instance_tree.edit(destination_section_value=person_user)
    self.tic()

    self.login(person_user.getUserId())
    self.changeSkin('Hal')
    fake_request = do_fake_request("GET")
    result = person_user.Person_getHateoasInstanceTreeList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(result, json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/foo",
        },
        "index": {
          "href": "urn:jio:get:%s" % person_user.getRelativeUrl(),
          "title": "Person"
        },
        "content": [{
          "href": "%s/ERP5Document_getHateoas" % \
              instance_tree.absolute_url(),
          "title": "Template Instance Tree"
        }],
      },
    }, indent=2))

class TestSlapOSInstanceTree_getHateoasInstanceList(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_getHateoasInstanceList_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_getHateoasInstanceList
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasInstanceList_wrong_ACCEPT(self):
    subscription = self._makeInstanceTree()
    fake_request = do_fake_request("GET")
    result = subscription.InstanceTree_getHateoasInstanceList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasInstanceList_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.InstanceTree_getHateoasInstanceList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasInstanceList_not_instance_tree_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.InstanceTree_getHateoasInstanceList(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasInstanceList_person_result(self):
    subscription = self._makeInstanceTree()
    instance= self._makeInstance()
    instance.edit(specialise_value=subscription)
    self.tic()

    fake_request = do_fake_request("GET")
    result = subscription.InstanceTree_getHateoasInstanceList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(result, json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/bar"
        },
        "content": [{
          "href": "%s/ERP5Document_getHateoas" % \
              instance.absolute_url(),
          "title": "Template Software Instance"
        }],
        "index": {
          "href": "urn:jio:get:%s" % subscription.getRelativeUrl(),
          "title": "Instance Tree"
        },
      },
    }, indent=2))

class TestSlapOSInstanceTree_getHateoasRootSoftwareInstance(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_getHateoasRootSoftwareInstance_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.InstanceTree_getHateoasRootSoftwareInstance
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasRootSoftwareInstance_wrong_ACCEPT(self):
    subscription = self._makeInstanceTree()
    fake_request = do_fake_request("GET")
    result = subscription.InstanceTree_getHateoasRootSoftwareInstance(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRootSoftwareInstance_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.InstanceTree_getHateoasRootSoftwareInstance(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRootSoftwareInstance_not_instance_tree_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.InstanceTree_getHateoasRootSoftwareInstance(
      REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRootSoftwareInstance_person_result(self):
    subscription = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=subscription, title=subscription.getTitle())
    subscription.edit(successor_value=instance)
    self.tic()

    fake_request = do_fake_request("GET")
    result = subscription.InstanceTree_getHateoasRootSoftwareInstance(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(result, json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/bar"
        },
        "content": [{
          "href": "%s/ERP5Document_getHateoas" % \
              instance.absolute_url(),
        }],
        "index": {
          "href": "urn:jio:get:%s" % subscription.getRelativeUrl(),
          "title": "Instance Tree"
        },
      },
    }, indent=2))

class TestSlapOSInstance_getHateoasNews(TestSlapOSHypermediaMixin):

  def _makeInstance(self):
    instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
        software_type=self.generateNewSoftwareType(),
        url_string=self.generateNewSoftwareReleaseUrl(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        connection_xml=self.generateSafeXml(),
    )
    self._addERP5Login(instance)
    self.tic()
    return instance

  @changeSkin('Hal')
  def test_getHateoasNewsInstance_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Instance_getHateoasNews
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasNewsInstance_wrong_ACCEPT(self):
    instance = self._makeInstance()
    fake_request = do_fake_request("GET")
    result = instance.Instance_getHateoasNews(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasNewsInstance_bad_method(self):
    instance = self._makeInstance()
    fake_request = do_fake_request("POST")
    result = instance.Instance_getHateoasNews(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasNewsInstance_not_instance_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Instance_getHateoasNews(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasNewsInstance_result(self):
    instance = self._makeInstance()
    fake_request = do_fake_request("GET")
    result = instance.Instance_getHateoasNews(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )

    self.assertEqual(json.loads(result), json.loads(json.dumps({
      'news': [{
        "user": "SlapOS Master",
        "text": "#error no data found for %s" % instance.getReference()
      }],
      '_links': {
        "self": {
          "href": "http://example.org/bar"
        },
        "index": {
          "href": "urn:jio:get:%s" % \
            instance.getRelativeUrl(),
          "title": "Software Instance"
        },
      },
    }, indent=2)))

class TestSlapOSInstance_getHateoasRelatedInstanceTree(TestSlapOSHypermediaMixin):

  def _makeInstance(self):
    instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
        software_type=self.generateNewSoftwareType(),
        url_string=self.generateNewSoftwareReleaseUrl(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        connection_xml=self.generateSafeXml(),
    )
    self._addERP5Login(instance)
    self.tic()
    return instance

  @changeSkin('Hal')
  def test_getHateoasRelatedInstanceTree_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Instance_getHateoasRelatedInstanceTree
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasRelatedInstanceTree_wrong_ACCEPT(self):
    instance = self._makeInstance()
    fake_request = do_fake_request("GET")
    result = instance.Instance_getHateoasRelatedInstanceTree(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRelatedInstanceTree_bad_method(self):
    instance = self._makeInstance()
    fake_request = do_fake_request("POST")
    result = instance.Instance_getHateoasRelatedInstanceTree(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRelatedInstanceTree_not_instance_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Instance_getHateoasRelatedInstanceTree(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/bar"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasRelatedInstanceTree_result(self):
    subscription = self._makeInstanceTree()
    instance= self._makeInstance()
    instance.edit(specialise_value=subscription)
    self.tic()
    fake_request = do_fake_request("GET")
    result = instance.Instance_getHateoasRelatedInstanceTree(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )

    self.assertEqual(json.loads(result), json.loads(json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/bar"
        },
        "index": {
          "href": "urn:jio:get:%s" % \
            instance.getRelativeUrl(),
          "title": "Software Instance"
        },
        "action_object_jump": {
          'href': "%s/ERP5Document_getHateoas" % subscription.getAbsoluteUrl(),
          'title': "Instance Tree"
        }
      },
    }, indent=2)))

class TestSlapOSInstance_getHateoasInformation(TestSlapOSHypermediaMixin):

  def _makeInstance(self):
    instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTHS-%s" % self.generateNewId(),
        software_type=self.generateNewSoftwareType(),
        url_string=self.generateNewSoftwareReleaseUrl(),
        instance_xml=self.generateSafeXml(),
        sla_xml=self.generateSafeXml(),
        connection_xml=self.generateSafeXml(),
    )
    self._addERP5Login(instance)
    self.tic()
    return instance

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoas_wrong_ACCEPT(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Instance_getHateoasInformation(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.Instance_getHateoasInformation(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_request_not_correct_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Instance_getHateoasInformation(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/foo"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_result(self):
    instance = self._makeInstance()
    instance.edit(url_string="http://foo.com/software.cfg")
    self.portal.portal_workflow._jumpToStateFor(instance,
        'start_requested')
    fake_request = do_fake_request("GET")
    result = instance.Instance_getHateoasInformation(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(json.loads(result), json.loads(json.dumps({
      'title': instance.getTitle(),
      'requested_state': 'started',
      'slave': False,
      'instance_guid': instance.getId(),
      'connection_dict': instance.getConnectionXmlAsDict(),
      'parameter_dict': instance.getInstanceXmlAsDict(),
      'software_type': instance.getSourceReference(),
      'sla_dict': instance.getSlaXmlAsDict(),
      '_links': {
        "self": {
          "href": "http://example.org/foo"
        },
        "software_release": {
          "href": "http://foo.com/software.cfg",
        },
        "index": {
          "href": "urn:jio:get:%s" % instance.getRelativeUrl(),
          "title": "Software Instance"
        },
      },
    }, indent=2)))

class TestSlapOSPerson_getHateoasComputeNodeList(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_getHateoasComputeNodeList_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.Person_getHateoasComputeNodeList
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoasComputeNodeList_wrong_ACCEPT(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Person_getHateoasComputeNodeList(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasComputeNodeList_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.Person_getHateoasComputeNodeList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasComputeNodeList_request_not_correct_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.Person_getHateoasComputeNodeList(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/foo"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoasComputeNodeList_result(self):
    person_user = self._makePerson()
    compute_node = self._makeComputeNode()
    compute_node.edit(source_administration_value=person_user)
    self.tic()
    fake_request = do_fake_request("GET")
    self.changeSkin('Hal')
    result = person_user.Person_getHateoasComputeNodeList(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(json.loads(result), json.loads(json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/foo"
        },
        "index": {
          "href": "urn:jio:get:%s" % \
            person_user.getRelativeUrl(),
          "title": "Person"
        },
        "content": [{
          "href": "%s/ERP5Document_getHateoas" % \
              compute_node.absolute_url(),
          "title": compute_node.getTitle()
        }],
      },
    }, indent=2)))

class TestSlapOSComputeNode_getHateoasSoftwareInstallationList(TestSlapOSHypermediaMixin):

  @changeSkin('Hal')
  def test_getSoftwareInstallationList_REQUEST_mandatory(self):
    self.assertRaises(
      Unauthorized,
      self.portal.ComputeNode_getHateoasSoftwareInstallationList
    )

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getSoftwareInstallationList_wrong_ACCEPT(self):
    fake_request = do_fake_request("GET")
    result = self.portal.ComputeNode_getHateoasSoftwareInstallationList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getSoftwareInstallationList_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.ComputeNode_getHateoasSoftwareInstallationList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getSoftwareInstallationList_request_not_correct_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.ComputeNode_getHateoasSoftwareInstallationList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/foo"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getSoftwareInstallationList_result(self):
    compute_node = self._makeComputeNode()
    software_installation = self._makeSoftwareInstallation()
    software_installation.edit(aggregate_value=compute_node, url_string='foo')
    self.tic()
    fake_request = do_fake_request("GET")
    result = compute_node.ComputeNode_getHateoasSoftwareInstallationList(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(json.loads(result), json.loads(json.dumps({
      '_links': {
        "self": {
          "href": "http://example.org/foo"
        },
        "content": [{
          "href": "%s/ERP5Document_getHateoas" % \
              software_installation.absolute_url(),
          "title": "foo"
        }],
        "index": {
          "href": "urn:jio:get:%s" % compute_node.getRelativeUrl(),
          "title": "Compute Node"
        },
      },
    }, indent=2)))

class TestSlapOSSoftwareInstallation_getHateoasInformation(TestSlapOSHypermediaMixin):

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/vnd+bar"')
  @changeSkin('Hal')
  def test_getHateoas_wrong_ACCEPT(self):
    fake_request = do_fake_request("GET")
    result = self.portal.SoftwareInstallation_getHateoasInformation(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 406)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_bad_method(self):
    fake_request = do_fake_request("POST")
    result = self.portal.SoftwareInstallation_getHateoasInformation(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 405)
    self.assertEqual(result, "")

  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_request_not_correct_context(self):
    fake_request = do_fake_request("GET")
    result = self.portal.SoftwareInstallation_getHateoasInformation(REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 403)
    self.assertEqual(result, "")

  @simulate('Base_getRequestUrl', '*args, **kwargs',
      'return "http://example.org/foo"')
  @simulate('Base_getRequestHeader', '*args, **kwargs',
            'return "application/hal+json"')
  @changeSkin('Hal')
  def test_getHateoas_result(self):
    software_installation = self._makeSoftwareInstallation()
    software_installation.edit(url_string="http://foo.com/software.cfg")
    self.portal.portal_workflow._jumpToStateFor(software_installation,
        'start_requested')
    fake_request = do_fake_request("GET")
    result = software_installation.SoftwareInstallation_getHateoasInformation(
        REQUEST=fake_request)
    self.assertEqual(fake_request.RESPONSE.status, 200)
    self.assertEqual(fake_request.RESPONSE.getHeader('Content-Type'),
      "application/hal+json"
    )
    self.assertEqual(json.loads(result), json.loads(json.dumps({
      'title': software_installation.getTitle(),
      'status': 'started',
      '_links': {
        "self": {
          "href": "http://example.org/foo"
        },
        "software_release": {
          "href": "http://foo.com/software.cfg",
        },
        "index": {
          "href": "urn:jio:get:%s" % software_installation.getRelativeUrl(),
          "title": "Software Installation"
        },
      },
    }, indent=2)))
