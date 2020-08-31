# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
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

import unittest
import random
from AccessControl import getSecurityManager
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from Products.PluggableAuthService.interfaces.plugins import\
                                                      IAuthenticationPlugin

class TestSlapOSSecurityMixin(SlapOSTestCaseMixin):

  def _generateRandomUniqueUserId(self, portal_type, search_key="user_id"):
    user_id = None
    while user_id is None:
      random_user_id = "test_%s_%s" % (
        portal_type.replace(" ", "_").lower(), random.random())
      result_list = self.portal.portal_catalog(
          portal_type=portal_type,
          **{search_key: random_user_id}
          )
      if not len(result_list):
        user_id = random_user_id
    return user_id

  def _generateRandomUniqueReference(self, portal_type):
    return self._generateRandomUniqueUserId(portal_type, "reference")

  def _assertUserExists(self, user_id, login, password):
    """Checks that a user with login and password exists and can log in to the
    system.
    """
    uf = self.getUserFolder()
    self.assertNotEqual(uf.getUserById(user_id, None), None)
    for _, plugin in uf._getOb('plugins').listPlugins(
                                IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                  {'login_portal_type': ('ERP5 Login', 'Certificate Login',
                                         'Facebook Login', 'Google Login'),
                   'external_login': login}) is not None:
        break
    else:
      self.fail("No plugin could authenticate '%s' with password '%s'" %
              (login, password))

  def _assertUserDoesNotExists(self, user_id, login, password):
    """Checks that a user with login and password does not exists and cannot
    log in to the system.
    """
    uf = self.getUserFolder()
    for plugin_name, plugin in uf._getOb('plugins').listPlugins(
                              IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                {'login_portal_type': ('ERP5 Login', 'Certificate Login'),
                 'external_login': login}) is not None:
        self.fail(
           "Plugin %s should not have authenticated '%s' with password '%s'" %
           (plugin_name, login, password))

class TestSlapOSComputerSecurity(TestSlapOSSecurityMixin):
  def test_active(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId('Computer')
    reference = self._generateRandomUniqueReference('Computer')

    computer = self.portal.computer_module.newContent(
      portal_type='Computer', reference=reference)
    computer.setUserId(user_id)
    computer.validate()
    computer.newContent(portal_type=login_portal_type,
                      reference=reference).validate()

    self.tic()

    self._assertUserExists(user_id, reference, None)

    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-COMPUTER'],
      user.getGroups())

  def test_inactive(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId('Computer')
    reference = self._generateRandomUniqueReference('Computer')

    computer = self.portal.computer_module.newContent(
      portal_type='Computer', reference=reference)
    computer.setUserId(user_id)
    computer.newContent(portal_type=login_portal_type,
                      reference=reference)
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)

  def test_active_backward_compatibility_with_erp5_login(self):
    self.test_active(login_portal_type="ERP5 Login")

  def test_inactive_backward_compatibility_with_erp5_login(self):
    self.test_inactive(login_portal_type="ERP5 Login")

class TestSlapOSSoftwareInstanceSecurity(TestSlapOSSecurityMixin):
  portal_type = 'Software Instance'
  def test_active(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId(self.portal_type)
    reference = self._generateRandomUniqueReference(self.portal_type)

    instance = self.portal.getDefaultModule(portal_type=self.portal_type)\
      .newContent(portal_type=self.portal_type, reference=reference)
    instance.setUserId(user_id)
    instance.validate()
    instance.newContent(portal_type=login_portal_type,
                      reference=reference).validate()
    self.tic()

    self._assertUserExists(user_id, reference, None)

    # instance w/o subscription is loggable and it has some roles
    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-INSTANCE'],
      user.getGroups())

    self.login()
    subscription_reference = self._generateRandomUniqueReference(
        'Hosting Suscription')
    subscription = self.portal.hosting_subscription_module.newContent(
        portal_type='Hosting Subscription',
        reference=subscription_reference)
    subscription.validate()
    instance.setSpecialise(subscription.getRelativeUrl())
    self.tic()

    # clear cache in order to reset calculation
    self.portal.portal_caches.clearAllCache()
    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-INSTANCE', subscription_reference],
      user.getGroups())

  def test_inactive(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId(self.portal_type)
    reference = self._generateRandomUniqueReference(self.portal_type)

    instance = self.portal.getDefaultModule(portal_type=self.portal_type)\
      .newContent(portal_type=self.portal_type, reference=reference)
    instance.setUserId(user_id)
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)

  def test_active_backward_compatibility_with_erp5_login(self):
    self.test_active(login_portal_type="ERP5 Login")

  def test_inactive_backward_compatibility_with_erp5_login(self):
    self.test_inactive(login_portal_type="ERP5 Login")

class TestSlapOSPersonSecurity(TestSlapOSSecurityMixin):
  def test_active(self, login_portal_type="Certificate Login"):    
    reference = self._generateRandomUniqueReference('Person')
    user_id = self._generateRandomUniqueUserId('Person')

    person = self.portal.person_module.newContent(
      portal_type='Person',
      reference=reference)
    person.setUserId(user_id)

    password = person.Person_generatePassword()
    person.newContent(portal_type='Assignment').open()
    if login_portal_type == "ERP5 Login":
      person.newContent(portal_type=login_portal_type,
                      reference=reference,
                      password=password).validate()
    else:
      person.newContent(portal_type=login_portal_type,
                      reference=reference).validate()

    self.tic()

    self._assertUserExists(user_id, reference, password)

    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet([], user.getGroups())


    # add to group category
    self.login()
    person.newContent(portal_type='Assignment', group='company').open()
    self.tic()

    self.tic()
    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['G-COMPANY'], user.getGroups())

    # add to role category
    self.login()
    person.newContent(portal_type='Assignment', role='member').open()
    self.tic()

    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-MEMBER', 'G-COMPANY'], user.getGroups())

  def test_inactive(self, login_portal_type="Certificate Login"):
    reference = self._generateRandomUniqueReference('Person')
    user_id = self._generateRandomUniqueReference('Person')
    
    person = self.portal.person_module.newContent(portal_type='Person',
      reference=reference)
    password = person.Person_generatePassword()

    self.tic()

    self._assertUserDoesNotExists(user_id, reference, password)

    if login_portal_type == "ERP5 Login":
      person.newContent(portal_type=login_portal_type,
                      reference=reference,
                      password=password).validate()
    else:
      person.newContent(portal_type=login_portal_type,
                      reference=reference).validate()
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, password)

  def test_active_erp5_login(self):
    self.test_active(login_portal_type="ERP5 Login")

  def test_inactive_erp5_login(self):
    self.test_inactive(login_portal_type="ERP5 Login")

  def test_active_facebook_login(self):
    self.test_active(login_portal_type="Facebook Login")

  def test_inactive_facebook_login(self):
    self.test_inactive(login_portal_type="Facebook Login")
  
  def test_active_google_login(self):
    self.test_active(login_portal_type="Google Login")

  def test_inactive_google_login(self):
    self.test_inactive(login_portal_type="Google Login")


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSComputerSecurity))
  suite.addTest(unittest.makeSuite(TestSlapOSSoftwareInstanceSecurity))
  suite.addTest(unittest.makeSuite(TestSlapOSPersonSecurity))
  return suite
