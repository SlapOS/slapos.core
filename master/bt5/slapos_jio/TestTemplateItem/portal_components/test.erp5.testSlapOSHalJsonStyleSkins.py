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

def fakeStopRequestedSlapState():
  return "stop_requested"

def fakeDestroyRequestedSlapState():
  return "destroy_requested"

class TestSlapOSHalJsonStyleMixin(SlapOSTestCaseMixinWithAbort):
  
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
      'state': state
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
    compute_node = self.portal.compute_node_module\
        .template_compute_node.Base_createCloneDocument(batch_mode=1)
    compute_node.edit(reference="TESTCOMP-%s" % compute_node.getId())
    compute_node.validate()

    compute_node.newContent(portal_type="Compute Partition",
                        title="slappart0", id="slappart0")
    compute_node.newContent(portal_type="Compute Partition",
                        title="slappart1", id="slappart1")

    self.tic()
    self.changeSkin('Hal')
    return compute_node
  
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
    expected_news_dict = {'instance': []}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_slave(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.setRootSlave(1)
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [], 'is_slave': 1}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.getSlapState = fakeStopRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [], 'is_stopped': 1}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    instance_tree = self._makeInstanceTree()
    instance_tree.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [], 'is_destroyed': 1}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [{'created_at': self.created_at,
                'no_data': 1,
                'since': self.created_at,
                'state': '',
                'text': '#error no data found for %s' % instance.getReference(),
                'user': 'SlapOS Master'}]}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_slave_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeSlaveInstance()
    instance.edit(specialise_value=instance_tree)
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': []}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_two_instance(self):
    instance_tree = self._makeInstanceTree()
    instance = self._makeInstance()
    instance.edit(specialise_value=instance_tree)
    instance0 = self._makeInstance()
    instance0.edit(specialise_value=instance_tree)
    
    self.tic()
    self.changeSkin('Hal')
    news_dict = instance_tree.InstanceTree_getNewsDict()
    expected_news_dict = {'instance': [{'created_at': self.created_at,
                'no_data': 1,
                'since': self.created_at,
                'state': '',
                'text': '#error no data found for %s' % instance0.getReference(),
                'user': 'SlapOS Master'},
              {'created_at': self.created_at,
               'no_data': 1,
               'since': self.created_at,
               'state': '',
               'text': '#error no data found for %s' % instance.getReference(),
               'user': 'SlapOS Master'}]}
    self.assertEqual(news_dict["instance"], expected_news_dict["instance"])
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestSoftwareInstance_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    instance = self._makeInstance()
    self._logFakeAccess(instance)
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict =  {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': '#access OK',
                          'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)


  def test_no_data(self):
    instance = self._makeInstance()
    self.changeSkin('Hal')

    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {'created_at': self.created_at,
      'no_data': 1,
      'since': self.created_at,
      'state': '',
      'text': '#error no data found for %s' % instance.getReference(),
      'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_slave(self):
    instance = self._makeSlaveInstance()
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {'is_slave': 1,
      'text': '#nodata is a slave %s' % instance.getReference(),
      'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    instance = self._makeInstance()
    instance.getSlapState = fakeStopRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {
      "user": "SlapOS Master",
      "text": "#nodata is an stopped instance %s" % instance.getReference(),
      "is_stopped": 1
    }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    instance = self._makeInstance()
    instance.getSlapState = fakeDestroyRequestedSlapState
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {
      "user": "SlapOS Master",
      "text": "#nodata is an destroyed instance %s" % instance.getReference(),
      "is_destroyed": 1
    }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)
class TestSoftwareInstallation_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation)
    news_dict = installation.SoftwareInstallation_getNewsDict()
    expected_news_dict =  {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': '#access OK',
                          'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation,
                        state='stop_requested')
    news_dict = installation.SoftwareInstallation_getNewsDict()
    installation.getSlapState = fakeStopRequestedSlapState

    expected_news_dict =  {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'stop_requested',
                           'text': '#access OK',
                          'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation,
                        state='destroy_requested')
    news_dict = installation.SoftwareInstallation_getNewsDict()
    installation.getSlapState = fakeDestroyRequestedSlapState

    expected_news_dict =  {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'destroy_requested',
                           'text': '#access OK',
                          'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    installation = self._makeSoftwareInstallation()
    news_dict = installation.SoftwareInstallation_getNewsDict()
    expected_news_dict = {'created_at': self.created_at,
      'no_data': 1,
      'since': self.created_at,
      'state': '',
      'text': '#error no data found for %s' % installation.getReference(),
      'user': 'SlapOS Master'}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestComputeNode_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    compute_node = self._makeComputeNode()
    self._logFakeAccess(compute_node)
    news_dict = compute_node.ComputeNode_getNewsDict()
    expected_news_dict =  {'compute_node': 
                           {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': '#access OK',
                          'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    compute_node = self._makeComputeNode()
    self._logFakeAccess(compute_node,
                        state='stop_requested')
    news_dict = compute_node.ComputeNode_getNewsDict()
    compute_node.getSlapState = fakeStopRequestedSlapState

    expected_news_dict =  {'compute_node': 
                            {'created_at': self.created_at,
                            'no_data_since_15_minutes': 0,
                            'no_data_since_5_minutes': 0,
                            'since': self.created_at,
                            'state': 'stop_requested',
                            'text': '#access OK',
                            'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    compute_node = self._makeComputeNode()
    self._logFakeAccess(compute_node,
                        state='destroy_requested')
    news_dict = compute_node.ComputeNode_getNewsDict()
    compute_node.getSlapState = fakeDestroyRequestedSlapState

    expected_news_dict =  {'compute_node': 
                           {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'destroy_requested',
                           'text': '#access OK',
                           'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    compute_node = self._makeComputeNode()
    news_dict = compute_node.ComputeNode_getNewsDict()
    expected_news_dict = {'compute_node': 
                           {'created_at': self.created_at,
                            'no_data': 1,
                            'since': self.created_at,
                            'state': '',
                            'text': '#error no data found for %s' % compute_node.getReference(),
                            'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_instance(self):
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(compute_node.slappart0)
    self.tic()
    
    self._logFakeAccess(compute_node)
    news_dict = compute_node.ComputeNode_getNewsDict()
    expected_news_dict =  {'compute_node': 
                           {u'created_at': u'%s' % self.created_at,
                            'no_data_since_15_minutes': 0,
                            'no_data_since_5_minutes': 0,
                            u'since': u'%s' % self.created_at,
                            u'state': u'start_requested',
                            u'text': u'#access OK',
                            u'user': u'SlapOS Master'},
                          'partition': {'slappart0': {'created_at': self.created_at,
                              'no_data': 1,
                              'since': self.created_at,
                              'state': '',
                              'text': '#error no data found for %s' % (instance.getReference()),
                              'user': 'SlapOS Master'}}
                          }
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestComputerNetwork_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    network = self._makeComputerNetwork()
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(compute_node.slappart0)
    compute_node.setSubordinationValue(network)

    self.tic()
    self._logFakeAccess(compute_node)
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict =  {'compute_node': 
                            { compute_node.getReference():
                              {u'created_at': u'%s' % self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               u'since': u'%s' % self.created_at,
                               u'state': u'start_requested',
                               u'text': u'#access OK',
                               u'user': u'SlapOS Master'}},
                            'partition':
                              { compute_node.getReference():
                                {'slappart0': {'created_at': self.created_at,
                                'no_data': 1,
                                'since': self.created_at,
                                'state': '',
                                'text': '#error no data found for %s' % (instance.getReference()),
                                'user': 'SlapOS Master'}
                                }
                              }
                            }
                          

    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    network = self._makeComputerNetwork()
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict = {'compute_node': {}, 'partition': {}}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestOrganisation_getNewsDict(TestSlapOSHalJsonStyleMixin):

  @simulate('Organisation_getComputeNodeTrackingList', 
    '*args, **kwargs', 'return context.fake_compute_node_list')
  def test(self):
    organisation = self._makeOrganisation()
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(compute_node.slappart0)
    organisation.fake_compute_node_list = [compute_node]

    self.tic()
    self._logFakeAccess(compute_node)
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict =  {'compute_node': 
                            { compute_node.getReference():
                              {u'created_at': u'%s' % self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               u'since': u'%s' % self.created_at,
                               u'state': u'start_requested',
                               u'text': u'#access OK',
                               u'user': u'SlapOS Master'}},
                            'partition':
                              { compute_node.getReference():
                                {'slappart0': {'created_at': self.created_at,
                                'no_data': 1,
                                'since': self.created_at,
                                'state': '',
                                'text': '#error no data found for %s' % (instance.getReference()),
                                'user': 'SlapOS Master'}
                                }
                              }
                            }
                          

    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    organisation = self._makeOrganisation()
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict = {'compute_node': {}, 'partition': {}}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestProject_getNewsDict(TestSlapOSHalJsonStyleMixin):

  @simulate('Project_getComputeNodeTrackingList', 
    '*args, **kwargs', 'return context.fake_compute_node_list')
  def test(self):
    project = self._makeProject()
    compute_node = self._makeComputeNode()
    instance = self._makeInstance()
    instance.setAggregateValue(compute_node.slappart0)
    project.fake_compute_node_list = [compute_node]

    self.tic()
    self._logFakeAccess(compute_node)
    news_dict = project.Project_getNewsDict()
    expected_news_dict =  {'compute_node': 
                            { compute_node.getReference():
                              {u'created_at': u'%s' % self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               u'since': u'%s' % self.created_at,
                               u'state': u'start_requested',
                               u'text': u'#access OK',
                               u'user': u'SlapOS Master'}},
                            'partition':
                              { compute_node.getReference():
                                {'slappart0': {'created_at': self.created_at,
                                'no_data': 1,
                                'since': self.created_at,
                                'state': '',
                                'text': '#error no data found for %s' % (instance.getReference()),
                                'user': 'SlapOS Master'}
                                }
                              }
                            }
                          

    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    project = self._makeProject()
    news_dict = project.Project_getNewsDict()
    expected_news_dict = {'compute_node': {}, 'partition': {}}
    self.assertEqual(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestPerson_newLogin(TestSlapOSHalJsonStyleMixin):
  def test_Person_newLogin_as_superuser(self):
    person = self._makePerson(user=0)
    self.assertEqual(0 , len(person.objectValues( portal_type="ERP5 Login")))

    self.assertRaises(Unauthorized, person.Person_newLogin, reference="a", password="b")

  def test_Person_newLogin_different_user(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    personx = self._makePerson(user=1)
    self.assertEqual(1 , len(personx.objectValues( portal_type="ERP5 Login")))

    self.login(person.getUserId())
    self.assertRaises(Unauthorized, personx.Person_newLogin, reference="a", password="b")

  def test_Person_newLogin_duplicated(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

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
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    self.login(person.getUserId())
    result = json.loads(person.Person_newLogin(reference="a",
                                    password="b"))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 406)
    self.assertEqual(str(result), 'Password does not comply with password policy')
    
  def test_Person_newLogin(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    self.login(person.getUserId())

    result = json.loads(person.Person_newLogin(reference="SOMEUNIQUEUSER%s" % self.generateNewId(),
                                    password=person.Person_generatePassword()))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)
    self.assertIn(person.getRelativeUrl(), result)
    
class TestPerson_get_revoke_Certificate(TestSlapOSHalJsonStyleMixin):
  def test_Person_getCertificate_unauthorized(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    self.assertEqual(person.Person_getCertificate(), {})
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 403)

  def test_Person_revokeCertificate_unauthorized(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    self.assertEqual(person.Person_revokeCertificate(), None)
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 403)


  def test_Person_get_revoke_Certificate(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))
 
    self.login(person.getUserId())
    response_dict = json.loads(person.Person_getCertificate())
    
    self.assertSameSet(response_dict.keys(), ["common_name", "certificate", "id", "key"])
    self.assertEqual(response_dict["common_name"], person.getUserId())
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)

    response_false = json.loads(person.Person_getCertificate())
    self.assertFalse(response_false)

    response_true = json.loads(person.Person_revokeCertificate())
    self.assertTrue(response_true)

    response_false = json.loads(person.Person_revokeCertificate())
    self.assertFalse(response_false)

    response_dict = json.loads(person.Person_getCertificate())
    
    self.assertSameSet(response_dict.keys(), ["common_name", "certificate", "id", "key"])
    self.assertEqual(response_dict["common_name"], person.getUserId())
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

    self.tic()
    self.changeSkin("Hal")
    self.assertEqual(json.loads(network.ComputerNetwork_hasComputeNode()), 1)

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

    self.login(person.getUserId())
    token_dict = json.loads(base.Base_getComputeNodeToken())

    self.assertSameSet(token_dict.keys(), ['access_token', 'command_line',
                                    'slapos_master_web', 'slapos_master_api'])

    self.assertEqual(token_dict['command_line'], "wget https://deploy.erp5.net/slapos ; bash slapos")
    self.assertIn("%s-" % (DateTime().strftime("%Y%m%d")) , token_dict['access_token'])
    self.assertEqual(token_dict['slapos_master_api'], "https://slap.vifib.com")
    self.assertEqual(token_dict['slapos_master_web'], base.absolute_url())
    
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
