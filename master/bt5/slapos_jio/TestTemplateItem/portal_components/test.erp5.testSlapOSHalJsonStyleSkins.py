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
    self.created_at = rfc1123_date(DateTime())
    self.changeSkin('Hal')

  def _logFakeAccess(self, reference, text="#access OK", state='start_requested'):
    value = json.dumps({
      'user': 'SlapOS Master',
      'created_at': '%s' % self.created_at,
      'text': '%s' % text,
      'since': '%s' % self.created_at,
      'state': state
    })
    memcached_dict = self.portal.Base_getSlapToolMemcachedDict()
    memcached_dict[reference] = value

  def _makePerson(self, **kw):
    person_user = self.makePerson(**kw)
    self.tic()
    self.changeSkin('Hal')
    return person_user

  def _makeHostingSubscription(self):
    hosting_subscription = self.portal.hosting_subscription_module\
        .template_hosting_subscription.Base_createCloneDocument(batch_mode=1)
    hosting_subscription.validate()
    self.tic()
    self.changeSkin('Hal')
    return hosting_subscription

  def _makeInstance(self):
    instance = self.portal.software_instance_module\
        .template_software_instance.Base_createCloneDocument(batch_mode=1)
    instance.edit(reference="TESTSOFTINST-%s" % instance.getId())
    instance.validate()
    self.changeSkin('Hal')
    self.tic()
    return instance

  def _makeSlaveInstance(self):
    instance = self.portal.software_instance_module\
        .template_slave_instance.Base_createCloneDocument(batch_mode=1)
    instance.validate()
    self.tic()
    return instance

  def _makeComputer(self):
    computer = self.portal.computer_module\
        .template_computer.Base_createCloneDocument(batch_mode=1)
    computer.edit(reference="TESTCOMP-%s" % computer.getId())
    computer.validate()

    computer.newContent(portal_type="Computer Partition",
                        title="slappart0", id="slappart0")
    computer.newContent(portal_type="Computer Partition",
                        title="slappart1", id="slappart1")

    self.tic()
    self.changeSkin('Hal')
    return computer
  
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

class TestHostingSubscription_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    hosting_subscription = self._makeHostingSubscription()
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': []}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_slave(self):
    hosting_subscription = self._makeHostingSubscription()
    hosting_subscription.setRootSlave(1)
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': [], 'is_slave': 1}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    hosting_subscription = self._makeHostingSubscription()
    hosting_subscription.getSlapState = fakeStopRequestedSlapState
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': [], 'is_stopped': 1}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    hosting_subscription = self._makeHostingSubscription()
    hosting_subscription.getSlapState = fakeDestroyRequestedSlapState
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': [], 'is_destroyed': 1}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_instance(self):
    hosting_subscription = self._makeHostingSubscription()
    instance = self._makeInstance()
    instance.edit(specialise_value=hosting_subscription)
    self.tic()
    self.changeSkin('Hal')
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': [{'no_data': 1,
                'text': '#error no data found for %s' % instance.getReference(),
                'user': 'SlapOS Master'}]}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_slave_instance(self):
    hosting_subscription = self._makeHostingSubscription()
    instance = self._makeSlaveInstance()
    instance.edit(specialise_value=hosting_subscription)
    self.tic()
    self.changeSkin('Hal')
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': []}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_two_instance(self):
    hosting_subscription = self._makeHostingSubscription()
    instance = self._makeInstance()
    instance.edit(specialise_value=hosting_subscription)
    instance0 = self._makeInstance()
    instance0.edit(specialise_value=hosting_subscription)
    
    self.tic()
    self.changeSkin('Hal')
    news_dict = hosting_subscription.HostingSubscription_getNewsDict()
    expected_news_dict = {'instance': [{'no_data': 1,
                'text': '#error no data found for %s' % instance0.getReference(),
                'user': 'SlapOS Master'},
              {'no_data': 1,
                'text': '#error no data found for %s' % instance.getReference(),
                'user': 'SlapOS Master'}]}
    self.assertEquals(news_dict["instance"], expected_news_dict["instance"])
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestSoftwareInstance_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    instance = self._makeInstance()
    self._logFakeAccess(instance.getReference())
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict =  {u'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': u'#access OK',
                          u'user': u'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)


  def test_no_data(self):
    instance = self._makeInstance()
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {'no_data': 1,
     'text': '#error no data found for %s' % instance.getReference(),
     'user': 'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_slave(self):
    instance = self._makeSlaveInstance()
    news_dict = instance.SoftwareInstance_getNewsDict()
    expected_news_dict = {'is_slave': 1,
      'text': '#nodata is a slave %s' % instance.getReference(),
      'user': 'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
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
    self.assertEquals(news_dict, expected_news_dict)
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
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestSoftwareInstallation_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation.getReference())
    news_dict = installation.SoftwareInstallation_getNewsDict()
    expected_news_dict =  {u'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': u'#access OK',
                          u'user': u'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation.getReference(),
                        state='stop_requested')
    news_dict = installation.SoftwareInstallation_getNewsDict()
    installation.getSlapState = fakeStopRequestedSlapState

    expected_news_dict =  {u'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'stop_requested',
                           'text': u'#access OK',
                          u'user': u'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    installation = self._makeSoftwareInstallation()
    self._logFakeAccess(installation.getReference(),
                        state='destroy_requested')
    news_dict = installation.SoftwareInstallation_getNewsDict()
    installation.getSlapState = fakeDestroyRequestedSlapState

    expected_news_dict =  {u'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'destroy_requested',
                           'text': u'#access OK',
                          u'user': u'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    installation = self._makeSoftwareInstallation()
    news_dict = installation.SoftwareInstallation_getNewsDict()
    expected_news_dict = {'no_data': 1,
     'text': '#error no data found for %s' % installation.getReference(),
     'user': 'SlapOS Master'}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestComputer_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    computer = self._makeComputer()
    self._logFakeAccess(computer.getReference())
    news_dict = computer.Computer_getNewsDict()
    expected_news_dict =  {'computer': 
                           {u'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'start_requested',
                           'text': u'#access OK',
                          u'user': u'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_stopped(self):
    computer = self._makeComputer()
    self._logFakeAccess(computer.getReference(),
                        state='stop_requested')
    news_dict = computer.Computer_getNewsDict()
    computer.getSlapState = fakeStopRequestedSlapState

    expected_news_dict =  {'computer': 
                            {'created_at': self.created_at,
                            'no_data_since_15_minutes': 0,
                            'no_data_since_5_minutes': 0,
                            'since': self.created_at,
                            'state': 'stop_requested',
                            'text': '#access OK',
                            'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_destroyed(self):
    computer = self._makeComputer()
    self._logFakeAccess(computer.getReference(),
                        state='destroy_requested')
    news_dict = computer.Computer_getNewsDict()
    computer.getSlapState = fakeDestroyRequestedSlapState

    expected_news_dict =  {'computer': 
                           {'created_at': self.created_at,
                           'no_data_since_15_minutes': 0,
                           'no_data_since_5_minutes': 0,
                           'since': self.created_at,
                           'state': 'destroy_requested',
                           'text': u'#access OK',
                           'user': u'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    computer = self._makeComputer()
    news_dict = computer.Computer_getNewsDict()
    expected_news_dict = {'computer': 
                           {'no_data': 1,
                            'text': '#error no data found for %s' % computer.getReference(),
                             'user': 'SlapOS Master'},
                          'partition': {}
                          }
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_with_instance(self):
    computer = self._makeComputer()
    instance = self._makeInstance()
    instance.setAggregateValue(computer.slappart0)
    self.tic()
    
    self._logFakeAccess(computer.getReference())
    news_dict = computer.Computer_getNewsDict()
    expected_news_dict =  {'computer': 
                           {'created_at': self.created_at,
                            'no_data_since_15_minutes': 0,
                            'no_data_since_5_minutes': 0,
                            'since': self.created_at,
                            'state': 'start_requested',
                            'text': '#access OK',
                            'user': 'SlapOS Master'},
                          'partition': {'slappart0': {'no_data': 1,
                              'text': '#error no data found for %s' % (instance.getReference()),
                              'user': 'SlapOS Master'}}
                          }
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestComputerNetwork_getNewsDict(TestSlapOSHalJsonStyleMixin):

  def test(self):
    network = self._makeComputerNetwork()
    computer = self._makeComputer()
    instance = self._makeInstance()
    instance.setAggregateValue(computer.slappart0)
    computer.setSubordinationValue(network)

    self.tic()
    self._logFakeAccess(computer.getReference())
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict =  {'computer': 
                            { computer.getReference():
                              {'created_at': self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               'since': self.created_at,
                               'state': 'start_requested',
                               'text': '#access OK',
                               'user': 'SlapOS Master'}
                            },
                          'partition':
                            { computer.getReference():
                              {'slappart0': {'no_data': 1,
                              'text': '#error no data found for %s' % (instance.getReference()),
                              'user': 'SlapOS Master'}
                              }
                            }
                          }

    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    network = self._makeComputerNetwork()
    self._logFakeAccess(network.getReference())
    news_dict = network.ComputerNetwork_getNewsDict()
    expected_news_dict = {'computer': {}, 'partition': {}}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestOrganisation_getNewsDict(TestSlapOSHalJsonStyleMixin):

  @simulate('Organisation_getComputerTrackingList', 
    '*args, **kwargs', 'return context.fake_computer_list')
  def test(self):
    organisation = self._makeOrganisation()
    computer = self._makeComputer()
    instance = self._makeInstance()
    instance.setAggregateValue(computer.slappart0)
    organisation.fake_computer_list = [computer]

    self.tic()
    self._logFakeAccess(computer.getReference())
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict =  {'computer': 
                            { computer.getReference():
                              {'created_at': self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               'since': self.created_at,
                               'state': 'start_requested',
                               'text': '#access OK',
                               'user': 'SlapOS Master'}
                            },
                          'partition':
                            { computer.getReference():
                              {'slappart0': {'no_data': 1,
                              'text': '#error no data found for %s' % (instance.getReference()),
                              'user': 'SlapOS Master'}
                              }
                            }
                          }

    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    organisation = self._makeOrganisation()
    news_dict = organisation.Organisation_getNewsDict()
    expected_news_dict = {'computer': {}, 'partition': {}}
    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

class TestProject_getNewsDict(TestSlapOSHalJsonStyleMixin):

  @simulate('Project_getComputerTrackingList', 
    '*args, **kwargs', 'return context.fake_computer_list')
  def test(self):
    project = self._makeProject()
    computer = self._makeComputer()
    instance = self._makeInstance()
    instance.setAggregateValue(computer.slappart0)
    project.fake_computer_list = [computer]

    self.tic()
    self._logFakeAccess(computer.getReference())
    news_dict = project.Project_getNewsDict()
    expected_news_dict =  {'computer': 
                            { computer.getReference():
                              {'created_at': self.created_at,
                               'no_data_since_15_minutes': 0,
                               'no_data_since_5_minutes': 0,
                               'since': self.created_at,
                               'state': 'start_requested',
                               'text': '#access OK',
                               'user': 'SlapOS Master'}
                            },
                          'partition':
                            { computer.getReference():
                              {'slappart0': {'no_data': 1,
                              'text': '#error no data found for %s' % (instance.getReference()),
                              'user': 'SlapOS Master'}
                              }
                            }
                          }

    self.assertEquals(news_dict, expected_news_dict)
    # Ensure it don't raise error when converting to JSON
    json.dumps(news_dict)

  def test_no_data(self):
    project = self._makeProject()
    news_dict = project.Project_getNewsDict()
    expected_news_dict = {'computer': {}, 'partition': {}}
    self.assertEquals(news_dict, expected_news_dict)
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
    self.assertEqual(result, 'Password value doest not comply with password policy')
    
  def test_Person_newLogin(self):
    person = self._makePerson(user=1)
    self.assertEqual(1 , len(person.objectValues( portal_type="ERP5 Login")))

    self.login(person.getUserId())

    result = json.loads(person.Person_newLogin(reference="SOMEUNIQUEUSER%s" % self.generateNewId(),
                                    password=person.Person_generatePassword()))
    
    self.assertEqual(self.portal.REQUEST.RESPONSE.getStatus(), 200)
    self.assertIn(person.getRelativeUrl(), result)
    
