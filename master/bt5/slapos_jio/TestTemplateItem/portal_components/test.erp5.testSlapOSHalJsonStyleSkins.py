# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2013-2019  Nexedi SA and Contributors.
#
# This program is free software: you can Use, Study, Modify and Redistribute
# it under the terms of the GNU General Public License version 3, or (at your
# option) any later version, as published by the Free Software Foundation.
#
# You can also Link and Combine this program with other software covered by
# the terms of any of the Free Software licenses or any of the Open Source
# Initiative approved licenses and Convey the resulting work. Corresponding
# source of such a combination shall include the source code for all other
# software used.
#
# This program is distributed WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See COPYING file for full licensing terms.
# See https://www.nexedi.com/licensing for rationale and options.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import \
  SlapOSTestCaseMixinWithAbort, simulate
from zExceptions import Unauthorized
from App.Common import rfc1123_date
from Products.ERP5Type.Cache import DEFAULT_CACHE_SCOPE
from DateTime import DateTime
import json
import transaction

def _decode_with_json(value):
  # Ensure value is serisalisable as json
  return json.loads(json.dumps(value))

def fakeStopRequestedSlapState():
  return "stop_requested"

def fakeDestroyRequestedSlapState():
  return "destroy_requested"

class TestSlapOSHalJsonStyleMixin(SlapOSTestCaseMixinWithAbort):

  def getMonitorUrl(self, context):
    if context.getSlapState() == fakeDestroyRequestedSlapState():
      return ''
    if context.getPortalType() in ["Software Instance", "Slave Instance"]:
      connection = context.getConnectionXmlAsDict()
      if connection and 'monitor-user' in connection and \
          'monitor-password' in connection and \
          'monitor-base-url' in connection:
        return 'https://monitor.app.officejs.com/#/?username=testuser&url=softinst-monitored/public/feeds&password=testpass&page=ojsm_dispatch&query=portal_type%3A%22Software%20Instance%22%20AND%20title%3A%22Template%20Software%20Instance%22%20AND%20specialise_title%3A%22Template%20Instance%20Tree%22'
      else:
        return ''
    else:
      soft_inst = context.getSuccessorValue()
      if soft_inst:
        connection = soft_inst.getConnectionXmlAsDict()
        if connection and 'monitor-user' in connection and \
          'monitor-password' in connection and \
          'monitor-base-url' in connection:
          return 'https://monitor.app.officejs.com/#/?username=testuser&url=softinst-monitored/public/feeds&password=testpass&page=ojsm_dispatch&query=portal_type%3A%22Instance%20Tree%22%20AND%20title%3A%22Template%20Instance%20Tree%22'
      return ''

  maxDiff = None
  def afterSetUp(self):
    SlapOSTestCaseMixinWithAbort.afterSetUp(self)
    d = DateTime()
    self.pinDateTime(d)

    self.created_at = rfc1123_date(d)
    self.changeSkin('Hal')


  def beforeTearDown(self):
    SlapOSTestCaseMixinWithAbort.beforeTearDown(self)
    self.unpinDateTime()

  def _logFakeAccess(self, document, text="#access OK", state='start_requested'):
    value = json.dumps({
      'user': 'SlapOS Master',
      'created_at': '%s' % self.created_at,
      'text': '%s' % text,
      'since': '%s' % self.created_at,
      'state': state,
      'reference': document.getReference(),
      'portal_type': document.getPortalType()
    })
    cache_duration = document._getAccessStatusCacheFactory().cache_duration
    document._getAccessStatusPlugin().set(document._getAccessStatusCacheKey(),
      DEFAULT_CACHE_SCOPE, value, cache_duration=cache_duration)

  def _makePerson(self, **kw):
    person_user = self.makePerson(**kw)
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
    instance.edit(reference="TESTSOFTINST-%s" % instance.getId())
    instance.validate()
    self.tic()
    self.changeSkin('Hal')
    return instance

  def _makeSlaveInstance(self):
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    instance.validate()
    self.tic()
    self.changeSkin('Hal')
    return instance

  def _makeComputeNode(self, owner=None, allocation_scope='open/public'):
    _, partition0 =SlapOSTestCaseMixinWithAbort._makeComputeNode(
      self, owner=owner, allocation_scope=allocation_scope
    )

    self.partition0 = partition0
    reference = 'TESTPART-%s' % self.generateNewId()
    self.partition1 = self.compute_node.newContent(
      portal_type="Compute Partition",
      title="slappart1", reference=reference, id="slappart1")

    self.partition1.markFree()
    self.partition1.validate()

    self.tic()
    self.changeSkin('Hal')
    return self.compute_node

  def _makeComputerNetwork(self):
    network = self.portal.computer_network_module.newContent()
    network.edit(reference="TESTNET-%s" % network.getId())
    network.validate()

    self.tic()
    self.changeSkin('Hal')
    return network

  def _makeProject(self):
    project = self.portal.project_module.newContent()
    project.edit(reference="TESTPROJ-%s" % project.getId())
    project.validate()

    self.tic()
    self.changeSkin('Hal')
    return project

  def _makeOrganisation(self):
    organisation = self.portal.organisation_module.newContent()
    organisation.edit(reference="TESTSITE-%s" % organisation.getId())
    organisation.validate()

    self.tic()
    self.changeSkin('Hal')
    return organisation

  def _makeSoftwareInstallation(self):
    software_installation = self.portal.software_installation_module\
        .template_software_installation.Base_createCloneDocument(batch_mode=1)
    software_installation.edit(
      reference="TESTSOFTINSTTT-%s" % software_installation.getId())

    software_installation.validate()
    self.tic()
    self.changeSkin('Hal')
    return software_installation

class TestInstanceTree_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    instance_tree = self._makeInstanceTree()
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {
      'instance': [],
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree)
    }
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_slave(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.setRootSlave(1)
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [],
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree),
      'is_slave': 1
    }
    self.assertEqual(news_dict,
                    _decode_with_json(expected_news_dict))

  def test_stopped(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.getSlapState = fakeStopRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [],
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree),
      'is_stopped': 1
    }
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_destroyed(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [],
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree),
      'is_destroyed': 1
    }
    self.assertEqual(_decode_with_json(news_dict),
                     _decode_with_json(expected_news_dict))

  def test_with_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree),
      'instance': [{'created_at': self.created_at,
                'no_data': 1,
                'portal_type': instance.getPortalType(),
                'reference': instance.getReference(),
                'since': self.created_at,
                'monitor_url': self.getMonitorUrl(instance),
                'state': '',
                'text': '#error no data found for %s' % instance.getReference(),
                'user': 'SlapOS Master'}]
    }
    self.assertEqual(_decode_with_json(news_dict),
                     _decode_with_json(expected_news_dict))

  def test_with_slave_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeSlaveInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'instance': [],
      'monitor_url': self.getMonitorUrl(instance_tree)
    }
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_with_two_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    instance0 = self._makeInstance()
    instance0.edit(specialise_value=instance_tree)
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {
      'portal_type': instance_tree.getPortalType(),
      'reference': instance_tree.getReference(),
      'title': instance_tree.getTitle(),
      'monitor_url': self.getMonitorUrl(instance_tree),
      'instance': [
        {'created_at': self.created_at,
          'no_data': 1,
          'portal_type': instance0.getPortalType(),
          'reference': instance0.getReference(),
          'since': self.created_at,
          'monitor_url': self.getMonitorUrl(instance0),
          'state': '',
          'text': '#error no data found for %s' % instance0.getReference(),
          'user': 'SlapOS Master'},
        {'created_at': self.created_at,
         'no_data': 1,
         'portal_type': instance.getPortalType(),
         'reference': instance.getReference(), 
         'since': self.created_at,
         'monitor_url': self.getMonitorUrl(instance),
         'state': '',
         'text': '#error no data found for %s' % instance.getReference(),
         'user': 'SlapOS Master'}]}
    self.assertEqual(_decode_with_json(news_dict["instance"]),
                    _decode_with_json(expected_news_dict["instance"]))


class TestSoftwareInstance_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    self._logFakeAccess(instance)
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict =  {'created_at': self.created_at,
      'no_data_since_15_minutes': 0,
      'no_data_since_5_minutes': 0,
      'portal_type': instance.getPortalType(),
      'reference': instance.getReference(),
      'monitor_url': self.getMonitorUrl(instance),
      'since': self.created_at,
      'state': 'start_requested',
      'text': '#access OK',
      'user': 'SlapOS Master'}
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))


  def test_no_data(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    self.changeSkin('Hal')

    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {'created_at': self.created_at,
      'no_data': 1,
      'portal_type': instance.getPortalType(),
      'reference': instance.getReference(),
      'since': self.created_at,
      'state': '',
      'text': '#error no data found for %s' % instance.getReference(),
      'monitor_url': self.getMonitorUrl(instance),
      'user': 'SlapOS Master'}

    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_slave(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeSlaveInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {
      'portal_type': instance.getPortalType(),
      'reference': instance.getReference(),
      'is_slave': 1,
      'text': '#nodata is a slave %s' % instance.getReference(),
      'monitor_url': 'https://monitor.app.officejs.com/#/?username=testuser&url=softinst-monitored/public/feeds&password=testpass&page=ojsm_dispatch&query=portal_type%3A%22Software%20Instance%22%20AND%20title%3A%22Template%20Slave%20Instance%22%20AND%20specialise_title%3A%22Template%20Instance%20Tree%22',
      'user': 'SlapOS Master'}
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_stopped(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance_tree.edit(successor_value=instance)
    instance.getSlapState = fakeStopRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {
      "portal_type": instance.getPortalType(),
      "reference": instance.getReference(),
      "user": "SlapOS Master",
      "text": "#nodata is an stopped instance %s" % instance.getReference(),
      'monitor_url': self.getMonitorUrl(instance),
      "is_stopped": 1
    }
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_destroyed(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {
      "portal_type": instance.getPortalType(),
      "reference": instance.getReference(),
      "user": "SlapOS Master",
      "text": "#nodata is an destroyed instance %s" % instance.getReference(),
      'monitor_url': self.getMonitorUrl(instance),
      "is_destroyed": 1
    }
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

class TestComputerNetwork_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    network = self._makeComputerNetwork()
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(self.partition0)
    compute_node.setSubordinationValue(network)

    self.tic()
    self._logFakeAccess(compute_node)
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict =  {'compute_node': (
                            { compute_node.getReference():
                              {u'created_at': u'%s' % self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               'portal_type': compute_node.getPortalType(),
                               'reference': compute_node.getReference(),
                               u'since': u'%s' % self.created_at,
                               u'state': u'start_requested',
                               u'text': u'#access OK',
                               u'user': u'SlapOS Master'}}
                            ),
                            'portal_type': network.getPortalType(),
                            'reference': network.getReference()
                            }

    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_no_data(self):
    network = self._makeComputerNetwork()
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict = {
      'compute_node': {},
      'portal_type': network.getPortalType(),
      'reference': network.getReference()}
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

class TestOrganisation_getNewsDict(TestSlapOSHalJsonStyleMixin):

  @simulate('Organisation_getComputeNodeTrackingList', 
    '*args, **kwargs', 'return context.fake_compute_node_list')
  def test(self):
    organisation = self._makeOrganisation()
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(self.partition0)
    organisation.fake_compute_node_list = [compute_node]

    self.tic()
    self._logFakeAccess(compute_node)
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict =  {
      'portal_type': 'Organisation',
      'reference': organisation.getReference(),
      'compute_node': 
        { compute_node.getReference():
          {u'created_at': u'%s' % self.created_at,
           'no_data_since_15_minutes': 0,
           'no_data_since_5_minutes': 0,
           'portal_type': compute_node.getPortalType(),
           'reference': compute_node.getReference(),
           u'since': u'%s' % self.created_at,
           u'state': u'start_requested',
           u'text': u'#access OK',
           u'user': u'SlapOS Master'}}
        }
                          

    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

  def test_no_data(self):
    organisation = self._makeOrganisation()
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict = {
      'compute_node': {},
      'portal_type': 'Organisation',
      'reference': organisation.getReference()}
    self.assertEqual(_decode_with_json(news_dict),
                    _decode_with_json(expected_news_dict))

class TestPerson_newLogin(TestSlapOSHalJsonStyleMixin):
  def test_Person_newLogin_as_superuser(self):
    person = self._makePerson(user=0)
    self.assertEqual(0 , len(person.objectValues(portal_type="ERP5 Login")))

    self.assertRaises(Unauthorized, person.Person_newLogin, reference="a", password="b")

  def test_Person_newLogin_different_user(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    personx = self._makePerson(user=1)
    self.assertEqual(1 , len(personx.objectValues(portal_type="ERP5 Login")))

    self.login(person.getUserId())
    self.assertRaises(Unauthorized, personx.Person_newLogin, reference="a", password="b")

  def test_Person_newLogin_duplicated(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    personx = self._makePerson(user=1)
    login_list = personx.objectValues(portal_type="ERP5 Login")
    self.assertEqual(1 , len(login_list))
    login = login_list[0].getReference()
    self.tic()
   
    self.login(person.getUserId())
    result = json.loads(person.Person_newLogin(reference=login,
                                    password="b"))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 406)
    self.assertEqual(result, 'Login already exists')

  def test_Person_newLogin_dont_comply(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    self.login(person.getUserId())
    result = json.loads(person.Person_newLogin(reference="a",
                                    password="b"))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 406)
    self.assertEqual(str(result), 'Password does not comply with password policy')
    
  def test_Person_newLogin(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    self.login(person.getUserId())

    result = json.loads(person.Person_newLogin(reference="SOMEUNIQUEUSER%s" % self.generateNewId(),
                                    password=person.Person_generatePassword()))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)
    self.assertIn(person.getRelativeUrl(), result)
    
class TestPerson_get_Certificate(TestSlapOSHalJsonStyleMixin):
  def test_Person_getCertificate_unauthorized(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))

    self.assertEqual(person.Person_getCertificate(), {})
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 403)

  def test_Person_get_Certificate(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues(portal_type="ERP5 Login")))
 
    self.login(person.getUserId())
    response_dict = json.loads(person.Person_getCertificate())
    self.assertEqual(1 , len(person.objectValues(portal_type="Certificate Login")))
    login = person.objectValues(portal_type="Certificate Login")[0]
    self.assertEqual("validated" , login.getValidationState())

    self.assertSameSet(response_dict.keys(), ["common_name", "certificate", "id", "key"])

    self.assertEqual(response_dict["id"], login.getDestinationReference())
    self.assertEqual(json.dumps(response_dict["common_name"]), json.dumps(login.getReference()))
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

    new_response_dict = json.loads(person.Person_getCertificate())
    self.assertTrue(new_response_dict)

    self.assertEqual(2 , len(person.objectValues(portal_type="Certificate Login")))
    new_login = [i for i in person.objectValues(portal_type="Certificate Login")
      if i.getUid() != login.getUid()][0]
    
    self.assertEqual("validated" , login.getValidationState())
    self.assertEqual("validated" , new_login.getValidationState())
    self.assertNotEqual(login.getReference(), new_login.getReference())
    self.assertNotEqual(login.getDestinationReference(), new_login.getDestinationReference())

    self.assertSameSet(new_response_dict.keys(), ["common_name", "certificate", "id", "key"])
    self.assertEqual(json.dumps(new_response_dict["common_name"]), json.dumps(new_login.getReference()))
    self.assertEqual(new_response_dict["id"], new_login.getDestinationReference())
    
    self.assertNotEqual(new_response_dict["common_name"], response_dict["common_name"])
    self.assertNotEqual(new_response_dict["id"], response_dict["id"])
    self.assertNotEqual(new_response_dict["key"], response_dict["key"])
    self.assertNotEqual(new_response_dict["certificate"], response_dict["certificate"])

    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

class TestPerson_testLoginExistence(TestSlapOSHalJsonStyleMixin):
  def test_Person_testLoginExistence(self, portal_type="ERP5 Login"):
    person = self._makePerson(user=0)
    self.assertFalse(person.Person_testLoginExistence(reference="oqidjqosidjqoisdjqsoijdqs"))
    self.assertFalse(person.Person_testLoginExistence(reference=person.getUserId()))

    login = self.generateNewId()
    login_doc = person.newContent(
      portal_type=portal_type,
      reference=login  
    )
    login_doc.validate()
    self.tic()
    self.changeSkin("Hal")
    self.assertFalse(person.Person_testLoginExistence(reference=person.getUserId()))
    self.assertTrue(person.Person_testLoginExistence(reference=login))
    login_doc.invalidate()

    self.tic()

    self.changeSkin("Hal")
    self.assertFalse(person.Person_testLoginExistence(reference=login))

  def test_Person_testLoginExistence_google(self):
    self.test_Person_testLoginExistence(portal_type="Google Login")

  def test_Person_testLoginExistence_facebook(self):
    self.test_Person_testLoginExistence(portal_type="Facebook Login")

class TestERP5Site_invalidate(TestSlapOSHalJsonStyleMixin):
  def test_ERP5Site_invalidate(self, portal_type="ERP5 Login"):
    person = self._makePerson(user=0)
    login = self.generateNewId()
    login_doc = person.newContent(
      portal_type=portal_type,
      reference=login  
    )
    login_doc.validate()
    self.tic()
    self.changeSkin("Hal")

    login_doc.ERP5Login_invalidate()
    self.assertEqual(login_doc.getValidationState(), 'invalidated')

    # It shouldn't raise
    login_doc.ERP5Login_invalidate()
    self.assertEqual(login_doc.getValidationState(), 'invalidated')

  def test_ERP5Site_invalidate_google(self):
    self.test_ERP5Site_invalidate(portal_type="Google Login")

  def test_ERP5Site_invalidate_facebook(self):
    self.test_ERP5Site_invalidate(portal_type="Facebook Login")


class TestComputeNode_get_revoke_Certificate(TestSlapOSHalJsonStyleMixin):
  def test_ComputeNode_getCertificate(self):
    compute_node = self._makeComputeNode()
    self.assertEqual(0, len(compute_node.objectValues(portal_type=["ERP5 Login", "Certificate Login"])))

    response_dict = json.loads(compute_node.ComputeNode_getCertificate())
    
    self.assertSameSet(response_dict.keys(), ["certificate", "key"])
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

    response_false = json.loads(compute_node.ComputeNode_getCertificate())
    self.assertFalse(response_false)

    response_true = json.loads(compute_node.ComputeNode_revokeCertificate())
    self.assertTrue(response_true)

    response_false = json.loads(compute_node.ComputeNode_revokeCertificate())
    self.assertFalse(response_false)

    response_dict = json.loads(compute_node.ComputeNode_getCertificate())
    
    self.assertSameSet(response_dict.keys(), ["certificate", "key"])
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

class TestComputerNetwork_invalidate(TestSlapOSHalJsonStyleMixin):

  def test_ComputerNetwork_invalidate(self):
    network = self._makeComputerNetwork()
    self.assertEqual(network.getValidationState(), "validated")

    self.changeSkin("Hal")
    network.ComputerNetwork_invalidate()
    self.assertEqual(network.getValidationState(), "invalidated")

    # Call again to ensure it doesn't raise
    network.ComputerNetwork_invalidate()
    self.assertEqual(network.getValidationState(), "invalidated")

class TestComputerNetwork_hasComputeNode(TestSlapOSHalJsonStyleMixin):

  def test_ComputerNetwork_hasComputeNode(self):
    network = self._makeComputerNetwork()
    self.assertEqual(json.loads(network.ComputerNetwork_hasComputeNode()), 0)

    compute_node = self._makeComputeNode()
    compute_node.setSubordinationValue(network)
    compute_node.setAllocationScopeValue(
      self.portal.portal_categories.allocation_scope.open.public)
    self.tic()
    self.changeSkin("Hal")
    self.assertEqual(json.loads(network.ComputerNetwork_hasComputeNode()), 1)
    compute_node.setAllocationScopeValue(
      self.portal.portal_categories.allocation_scope.close.forever)
    self.tic()
    self.changeSkin("Hal")
    self.assertEqual(json.loads(network.ComputerNetwork_hasComputeNode()), 0)
    


class TestBase_getCredentialToken(TestSlapOSHalJsonStyleMixin):

  def test_Base_getCredentialToken(self):
    person = self._makePerson()
    base = self.portal.web_site_module.hostingjs

    self.assertRaises(AttributeError, base.Base_getCredentialToken)

    self.login(person.getUserId())

    token_dict = json.loads(base.Base_getCredentialToken())

    self.assertEqual(token_dict.keys(), ["access_token", "command_line"])
    self.assertEqual(token_dict['command_line'], "slapos configure client")

    self.assertIn("%s-" % (DateTime().strftime("%Y%m%d")) , token_dict['access_token'])

    self.login()
    token = self.portal.access_token_module[token_dict['access_token']]

    self.assertTrue(
      token.getUrlString().endswith("Person_getCertificate"))

    self.assertEqual(token.getAgentValue(), person)
    self.assertEqual("One Time Restricted Access Token", token.getPortalType())

class TestBase_getComputeNodeToken(TestSlapOSHalJsonStyleMixin):

  def test_Base_getComputeNodeToken(self):
    person = self._makePerson()
    base = self.portal.web_site_module.hostingjs

    # On certain environments or sub-projects this value
    # can be customized.
    slapos_master_web_url = base.getLayoutProperty(
      "configuration_slapos_master_web_url",
      default=base.absolute_url())

    self.login(person.getUserId())
    token_dict = json.loads(base.Base_getComputeNodeToken())

    self.assertSameSet(token_dict.keys(), ['access_token', 'command_line',
                                    'slapos_master_web', 'slapos_master_api'])

    self.assertEqual(token_dict['command_line'], "wget https://deploy.erp5.net/slapos ; bash slapos")
    self.assertIn("%s-" % (DateTime().strftime("%Y%m%d")) , token_dict['access_token'])
    self.assertEqual(token_dict['slapos_master_api'], "https://slap.vifib.com")
    self.assertEqual(token_dict['slapos_master_web'], slapos_master_web_url)
    
    self.login()
    token = self.portal.access_token_module[token_dict["access_token"]]

    self.assertIn("/Person_requestComputer", token.getUrlString())

    self.assertEqual(token.getAgentValue(), person)
    self.assertEqual("One Time Restricted Access Token", token.getPortalType())

class TestInstanceTree_edit(TestSlapOSHalJsonStyleMixin):

  def afterSetUp(self):
    TestSlapOSHalJsonStyleMixin.afterSetUp(self)
    self.changeSkin('Hal')

  def test_InstanceTree_edit(self):
    self._makeTree()
    self.instance_tree.edit(
      monitor_scope="enabled",
      upgrade_scope="auto",
      short_title="X",
      description="Y"
    )

    original_parameter = self.instance_tree.getTextContent()
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription()
    )

    self.assertEqual("enabled", self.instance_tree.getMonitorScope())
    self.assertEqual("auto", self.instance_tree.getUpgradeScope())
    self.assertEqual("X", self.instance_tree.getShortTitle())
    self.assertEqual("Y", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title="X1",
      description="Y1",
      monitor_scope="disabled",
      upgrade_scope="disabled"
    )

    self.assertEqual("disabled", self.instance_tree.getMonitorScope())
    self.assertEqual("disabled", self.instance_tree.getUpgradeScope())
    self.assertEqual("X1", self.instance_tree.getShortTitle())
    self.assertEqual("Y1", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    # Check if owner can edit it 
    self.logout()
    self.login(self.person_user.getUserId())
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription()
    )

    self.assertEqual("disabled", self.instance_tree.getMonitorScope())
    self.assertEqual("disabled", self.instance_tree.getUpgradeScope())
    self.assertEqual("X1", self.instance_tree.getShortTitle())
    self.assertEqual("Y1", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title="X2",
      description="Y2",
      monitor_scope="enabled",
      upgrade_scope="auto"
    )

    self.assertEqual("enabled", self.instance_tree.getMonitorScope())
    self.assertEqual("auto", self.instance_tree.getUpgradeScope())
    self.assertEqual("X2", self.instance_tree.getShortTitle())
    self.assertEqual("Y2", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

  def test_InstanceTree_edit_request(self):
    self._makeTree()
    kw = dict(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription())

    original_parameter = self.instance_tree.getTextContent()
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(**kw)
    
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    new_parameter = self.generateSafeXml()
    kw['text_content'] = new_parameter

    self.instance_tree.InstanceTree_edit(**kw)

    self.assertNotEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.assertEqual(new_parameter,
      self.instance_tree.getTextContent())

    transaction.commit()
    # Check if owner can edit it 
    self.logout()
    self.login(self.person_user.getUserId())
    self.changeSkin("Hal")

    original_parameter = new_parameter
    new_parameter = self.generateSafeXml()
    kw['text_content'] = new_parameter

    self.instance_tree.InstanceTree_edit(**kw)

    self.assertNotEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.assertEqual(new_parameter,
      self.instance_tree.getTextContent())

  def test_InstanceTree_edit_shared_instance(self):
    self._makeTree()
    project = self._makeProject()
    self.instance_tree.edit(
      monitor_scope="enabled",
      upgrade_scope="auto",
      short_title="X",
      description="Y"
    )

    self.person_user.newContent(
      portal_type="Assignment",
      destination_project_value=project
    ).open()

    another_person = self._makePerson(user=1)
    another_person.newContent(
      portal_type="Assignment",
      destination_project_value=project
    ).open()

    # Place instances on the project
    self.logout()
    self.login(self.person_user.getUserId())
    self.assertEqual(self.instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl()), None)
    self.login()
    self.tic()
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), project)

    original_parameter = self.instance_tree.getTextContent()
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription()
    )

    self.assertEqual("enabled", self.instance_tree.getMonitorScope())
    self.assertEqual("auto", self.instance_tree.getUpgradeScope())
    self.assertEqual("X", self.instance_tree.getShortTitle())
    self.assertEqual("Y", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title="X1",
      description="Y1",
      monitor_scope="disabled",
      upgrade_scope="disabled"
    )

    self.assertEqual("disabled", self.instance_tree.getMonitorScope())
    self.assertEqual("disabled", self.instance_tree.getUpgradeScope())
    self.assertEqual("X1", self.instance_tree.getShortTitle())
    self.assertEqual("Y1", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    # Check if owner can edit it 
    self.logout()
    self.login(self.person_user.getUserId())
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription()
    )

    self.assertEqual("disabled", self.instance_tree.getMonitorScope())
    self.assertEqual("disabled", self.instance_tree.getUpgradeScope())
    self.assertEqual("X1", self.instance_tree.getShortTitle())
    self.assertEqual("Y1", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title="X2",
      description="Y2",
      monitor_scope="enabled",
      upgrade_scope="auto"
    )

    self.assertEqual("enabled", self.instance_tree.getMonitorScope())
    self.assertEqual("auto", self.instance_tree.getUpgradeScope())
    self.assertEqual("X2", self.instance_tree.getShortTitle())
    self.assertEqual("Y2", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.logout()
    self.login(another_person.getUserId())
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription()
    )

    self.assertEqual("enabled", self.instance_tree.getMonitorScope())
    self.assertEqual("auto", self.instance_tree.getUpgradeScope())
    self.assertEqual("X2", self.instance_tree.getShortTitle())
    self.assertEqual("Y2", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.instance_tree.InstanceTree_edit(
      text_content=self.instance_tree.getTextContent(),
      short_title="X3",
      description="Y3",
      monitor_scope="disabled",
      upgrade_scope="disabled"
    )

    self.assertEqual("disabled", self.instance_tree.getMonitorScope())
    self.assertEqual("disabled", self.instance_tree.getUpgradeScope())
    self.assertEqual("X3", self.instance_tree.getShortTitle())
    self.assertEqual("Y3", self.instance_tree.getDescription())
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())


  def test_InstanceTree_edit_shared_instance_request(self):
    self._makeTree()
    project = self._makeProject()
    self.instance_tree.edit(
      monitor_scope="enabled",
      upgrade_scope="auto",
      short_title="X",
      description="Y"
    )

    self.person_user.newContent(
      portal_type="Assignment",
      destination_project_value=project
    ).open()

    another_person = self._makePerson(user=1)
    another_person.newContent(
      portal_type="Assignment",
      destination_project_value=project
    ).open()

    # Place instances on the project
    self.logout()
    self.login(self.person_user.getUserId())
    self.assertEqual(self.instance_tree.InstanceTree_createMovement(
      destination_project=project.getRelativeUrl()), None)
    self.login()
    self.tic()
    self.assertEqual(self.instance_tree.Item_getCurrentProjectValue(), project)
    kw = dict(
      text_content=self.instance_tree.getTextContent(),
      short_title=self.instance_tree.getShortTitle(),
      description=self.instance_tree.getDescription())

    original_parameter = self.instance_tree.getTextContent()
    self.changeSkin("Hal")
    self.instance_tree.InstanceTree_edit(**kw)
    self.assertEqual(original_parameter,
      self.instance_tree.getTextContent())

    new_parameter = self.generateSafeXml()
    kw['text_content'] = new_parameter

    self.instance_tree.InstanceTree_edit(**kw)
    self.assertNotEqual(original_parameter,
      self.instance_tree.getTextContent())
    self.assertEqual(new_parameter,
      self.instance_tree.getTextContent())

    transaction.commit()
    # Check if owner can edit it
    self.logout()
    self.login(self.person_user.getUserId())
    self.changeSkin("Hal")

    original_parameter = new_parameter
    new_parameter = self.generateSafeXml()
    kw['text_content'] = new_parameter

    self.instance_tree.InstanceTree_edit(**kw)

    self.assertNotEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.assertEqual(new_parameter,
      self.instance_tree.getTextContent())

    transaction.commit()
    self.login(another_person.getUserId())
    self.changeSkin("Hal")

    original_parameter = new_parameter
    new_parameter = self.generateSafeXml()
    kw['text_content'] = new_parameter

    self.instance_tree.InstanceTree_edit(**kw)

    self.assertNotEqual(original_parameter,
      self.instance_tree.getTextContent())

    self.assertEqual(new_parameter,
      self.instance_tree.getTextContent())

class TestSoftwareInstance_getConnectionParameterList(TestSlapOSHalJsonStyleMixin):
  
  def testSoftwareInstance_getConnectionParameterList(self):
    instance = self._makeInstance()
    xml_sample = """<?xml version="1.0" encoding="utf-8"?>
<instance>
<parameter id="p0">ABC</parameter>
<parameter id="p1">DEF</parameter>
</instance>"""
    instance.edit(connection_xml=xml_sample)

    # Place instances on the project
    self.logout()
    self.login()

    self.changeSkin("Hal")
    self.assertEqual(
      len(instance.SoftwareInstance_getConnectionParameterList()),
      2)
    self.assertEqual(
      instance.SoftwareInstance_getConnectionParameterList(raw=True),
      [{"connection_key": "p0", "connection_value": "ABC"},
       {"connection_key": "p1", "connection_value": "DEF"}]
      )

    xml_sample = """<?xml version="1.0" encoding="utf-8"?>
<instance>
<parameter id="_">{"p0": "ABC", "p1": "DEF"}</parameter>
</instance>"""
    instance.edit(connection_xml=xml_sample)

    # Place instances on the project
    self.logout()
    self.login()

    self.changeSkin("Hal")
    self.assertEqual(
      len(instance.SoftwareInstance_getConnectionParameterList()),
      2)
    self.assertEqual(
      instance.SoftwareInstance_getConnectionParameterList(raw=True),
      [{"connection_key": "p0", "connection_value": "ABC"},
       {"connection_key": "p1", "connection_value": "DEF"}]
      )

class TestBase_getAttentionPointList(TestSlapOSHalJsonStyleMixin):

  def afterSetUp(self):
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    TestSlapOSHalJsonStyleMixin.afterSetUp(self)

  def test_Base_getAttentionPointList_no_cloud_contract(self):
    self.login()
    expected_list = [{"text": "Your Contract is Deactivated",
      'page': "slap_request_contract_activation"}]
    self.assertEqual(expected_list,
      json.loads(
        self.portal.instance_tree_module.Base_getAttentionPointList()))

    person = self._makePerson(user=1)
    self.tic()

    self.login(person.getUserId())
    expected_list = [{"text": "Your Contract is Deactivated",
      'page': "slap_request_contract_activation"}]
    self.assertEqual(expected_list,
      json.loads(person.Base_getAttentionPointList()))

    self.login()
    instance_tree = self._makeInstanceTree()
    self.tic()
    expected_list = [{"text": "Your Contract is Deactivated",
      'page': "slap_request_contract_activation"}]
    self.assertEqual(expected_list,
      json.loads(instance_tree.Base_getAttentionPointList()))

  def test_Base_getAttentionPointList_support_request_related_to_compute_node(self):
    document = self._makeComputeNode()
    self.login()
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)
    ticket.setAggregateValue(document)
    ticket.submit()

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    ticket.validate()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    ticket.suspend()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)
    self.assertIn({"text": "Ticket waiting your response", 
                   "link": ticket.getRelativeUrl()},
                   attention_point_list)

    ticket.invalidate()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

  def test_Base_getAttentionPointList_support_request_related_to_instance_tree(self):
    self.login()
    document = self._makeInstanceTree()
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)
    ticket.setAggregateValue(document)
    ticket.submit()

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    # 1 is due cloud contract
    self.assertEqual(len(attention_point_list), 1)

    ticket.validate()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)

    ticket.suspend()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 2)
    self.assertIn({"text": "Ticket waiting your response", 
                   "link": ticket.getRelativeUrl()},
                   attention_point_list)

    ticket.invalidate()
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(document.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)

  def test_Base_getAttentionPointList_regularisation_request(self):
    support_request_module = self.portal.support_request_module
    self.login()
    ticket = self.portal.regularisation_request_module.newContent(\
                        title="Test Regularisation Request %s" % self.new_id)
    person = self._makePerson(user=1)
    ticket.setDestinationDecision(person.getRelativeUrl())                    
    ticket.submit()

    self.tic()
    self.login(person.getUserId())
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    self.login()
    ticket.validate()
    self.login(person.getUserId())

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    self.login()
    ticket.suspend()
    self.login(person.getUserId())

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)
    self.assertEqual(
      attention_point_list[0]["text"],
      "Regularisation waiting your response")
    self.assertEqual(
      attention_point_list[0]["link"],
      ticket.getRelativeUrl())

    self.login()
    ticket.invalidate()
    self.login(person.getUserId())

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

  def test_Base_getAttentionPointList_support_request(self):
    support_request_module = self.portal.support_request_module
    self.login()
    ticket = self.portal.support_request_module.newContent(\
                        title="Test Support Request %s" % self.new_id)
    person = self._makePerson(user=1)
    ticket.setDestinationDecision(person.getRelativeUrl())                    
    ticket.submit()

    self.tic()
    self.login(person.getUserId())
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    self.login()
    ticket.validate()
    self.login(person.getUserId())
    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    self.login()
    ticket.suspend()
    self.tic()
    self.login(person.getUserId())

    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)
    self.assertEqual(
      attention_point_list[0]["text"],
      "Ticket waiting your response")
    self.assertEqual(
      attention_point_list[0]["link"],
      ticket.getRelativeUrl())

    self.login()
    ticket.invalidate()
    self.login(person.getUserId())

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

  def test_Base_getAttentionPointList_upgrade_decision(self):
    support_request_module = self.portal.support_request_module
    self.login()
    ticket = self.portal.upgrade_decision_module.newContent(\
                        title="Test Upgrade Decision %s" % self.new_id)
    person = self._makePerson(user=1)
    ticket.setDestinationDecision(person.getRelativeUrl())                    

    self.tic()
    self.login(person.getUserId())
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

    self.login()
    ticket.confirm()
    self.tic()
    self.login(person.getUserId())

    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(len(attention_point_list), 1)
    self.assertEqual(
      attention_point_list[0]["text"],
      "Please Upgrade this service")
    self.assertEqual(
      attention_point_list[0]["link"],
      ticket.getRelativeUrl())

    self.login()
    ticket.start()
    self.login(person.getUserId())

    self.tic()
    self.changeSkin("Hal")
    attention_point_list = json.loads(
      support_request_module.Base_getAttentionPointList())
    self.assertEqual(attention_point_list, [])

class TestInstanceTree_getFastInputDict(TestSlapOSHalJsonStyleMixin):

  def afterSetUp(self):
    self.instance_tree = self.portal.instance_tree_module.newContent(
      portal_type="Instance Tree"
    )
    self.software_instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance"
    )
    TestSlapOSHalJsonStyleMixin.afterSetUp(self)

  def testInstanceTree_getFastInputDict_noUrlString(self):
    self.assertEqual({},
      self.instance_tree.InstanceTree_getFastInputDict())
    
  def testInstanceTree_getFastInputDict_re6st_no_instance(self):
    self.instance_tree.setUrlString(
      self.portal.software_release_module.re6st.getUrlString())
    self.assertEqual({},
      self.instance_tree.InstanceTree_getFastInputDict())

  def testInstanceTree_getFastInputDict_frontend_no_instance(self):
    self.instance_tree.setUrlString(
      self.portal.software_release_module.frontend.getUrlString())
    self.assertEqual({},
      self.instance_tree.InstanceTree_getFastInputDict())

  def testInstanceTree_getFastInputDict_slave_re6st(self):
    self.instance_tree.setRootSlave(True)
    self.instance_tree.setUrlString(
      self.portal.software_release_module.re6st.getUrlString())
    slave_instance = self.portal.software_instance_module.newContent(
      portal_type="Slave Instance",
      specialise_value=self.instance_tree
    )
    self.instance_tree.setSuccessorValue(slave_instance)
    self.assertEqual({},
      self.instance_tree.InstanceTree_getFastInputDict())

  def testInstanceTree_getFastInputDict_slave_frontend(self):
    self.instance_tree.setRootSlave(True)
    slave_instance = self.portal.software_instance_module.newContent(
      portal_type="Slave Instance",
      specialise_value=self.instance_tree
    )
    self.instance_tree.setSuccessorValue(slave_instance)
    self.instance_tree.setUrlString(
      self.portal.software_release_module.frontend.getUrlString())
    self.assertEqual({},
      self.instance_tree.InstanceTree_getFastInputDict())

  def testInstanceTree_getFastInputDict_re6st(self):
    self.instance_tree.setUrlString(
      self.portal.software_release_module.re6st.getUrlString())
    software_instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      specialise_value=self.instance_tree,
      reference="TESTSOFTINST-%s" % self.generateNewId()
    )
    self.instance_tree.setSuccessorValue(software_instance)
    self.instance_tree.setUrlString(
      self.portal.software_release_module.re6st.getUrlString())
    self.assertEqual({
      'enabled': True,
      'sla_xml': '<parameter id="instance_guid">%s</parameter>' % software_instance.getReference()
    }, self.instance_tree.InstanceTree_getFastInputDict())

  def testInstanceTree_getFastInputDict_frontend(self):
    software_instance = self.portal.software_instance_module.newContent(
      portal_type="Software Instance",
      specialise_value=self.instance_tree,
      reference="TESTSOFTINST-%s" % self.generateNewId()
    )
    self.instance_tree.setSuccessorValue(software_instance)
    self.instance_tree.setUrlString(
      self.portal.software_release_module.frontend.getUrlString())
    self.assertEqual({
      'enabled': True,
      'sla_xml': '<parameter id="instance_guid">%s</parameter>' % software_instance.getReference()
    }, self.instance_tree.InstanceTree_getFastInputDict())


class TestSoftwareProduct_getSoftwareReleaseAsHateoas(TestSlapOSHalJsonStyleMixin):

  @simulate('SoftwareProduct_getSortedSoftwareReleaseList', 
    'software_product_reference=None, software_release_url=None, strict=None', """
assert software_product_reference == 'fake'
assert software_release_url is None
assert strict is None
return context.REQUEST['test_software_release_list']""")
  def test_product_reference(self):

    sr = self._makeSoftwareRelease()
    self.changeSkin('RJS')

    self.portal.REQUEST['test_software_release_list'] = [sr]
 
    self.assertEqual(
      sr.getRelativeUrl(),
      json.loads(
        self.portal.SoftwareProduct_getSoftwareReleaseAsHateoas("product.fake"))
    )

  @simulate('SoftwareProduct_getSortedSoftwareReleaseList', 
    'software_product_reference=None, software_release_url=None, strict=None', """
assert software_product_reference is None
assert software_release_url == 'fake'
assert strict is False
return context.REQUEST['test_software_release_list']""")
  def test_software_release(self):

    sr = self._makeSoftwareRelease()
    self.changeSkin('RJS')

    self.portal.REQUEST['test_software_release_list'] = [sr]
 
    self.assertEqual(
      sr.getRelativeUrl(),
      json.loads(
        self.portal.SoftwareProduct_getSoftwareReleaseAsHateoas("fake"))
    )

  @simulate('SoftwareProduct_getSortedSoftwareReleaseList', 
    'software_product_reference=None, software_release_url=None, strict=None', """
assert software_product_reference is None
assert software_release_url == 'fake'
assert strict is True
return []""")
  def test_software_release_not_found(self):

    self.changeSkin('RJS')
    self.assertEqual(
      '',
      json.loads(
        self.portal.SoftwareProduct_getSoftwareReleaseAsHateoas("fake", True))
    )

class TestSoftwareInstance_getAllocationInformation(TestSlapOSHalJsonStyleMixin):

  def test_SoftwareInstance_getAllocationInformation_not_allocated(self):
    self._makeTree()
    self.changeSkin('RJS')

    self.login(self.person_user.getUserId())
    self.assertEqual("Not allocated",
      self.software_instance.SoftwareInstance_getAllocationInformation())

  def test_SoftwareInstance_getAllocationInformation(self):
    computer_owner = self._makePerson(user=1)
    self._makeComputeNode(owner=computer_owner)

    self._makeComplexComputeNode(person=computer_owner)
    started_instance = self.compute_node.partition1.getAggregateRelatedValue(
        portal_type='Software Instance')
    self.changeSkin('RJS')

    self.login(computer_owner.getUserId())
    self.assertEqual("%s (partition1)" % self.compute_node.getReference(),
      started_instance.SoftwareInstance_getAllocationInformation())

  def test_SoftwareInstance_getAllocationInformation_restricted_information(self):
    computer_owner = self._makePerson(user=1)
    self._makeComputeNode(owner=computer_owner)

    requester = self._makePerson(user=1)
    self._makeComplexComputeNode(person=requester)
    started_instance = self.compute_node.partition1.getAggregateRelatedValue(
        portal_type='Software Instance')

    # ensure it dont have good admin assignment
    for assignment in requester.contentValues(portal_type="Assignment"):
      assignment.setGroup(None)
      assignment.setRole("member")
    self.tic()
    self.changeSkin('RJS')

    self.login(requester.getUserId())
    self.assertEqual("Restricted information",
      started_instance.SoftwareInstance_getAllocationInformation())
