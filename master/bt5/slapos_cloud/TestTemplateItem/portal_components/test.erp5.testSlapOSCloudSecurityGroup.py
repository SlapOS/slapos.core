# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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
          limit=[0, 1],
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
    uf = self.portal.acl_users
    self.assertNotEqual(uf.getUserById(user_id, None), None)
    for _, plugin in uf._getOb('plugins').listPlugins(
                                IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                  {'login_portal_type': ('ERP5 Login', 'Certificate Login'),
                   'external_login': login}) is not None:
        break
    else:
      self.fail("No plugin could authenticate '%s' with password '%s'" %
              (login, password))

  def _assertUserDoesNotExists(self, user_id, login, password):
    """Checks that a user with login and password does not exists and cannot
    log in to the system.
    """
    uf = self.portal.acl_users
    for plugin_name, plugin in uf._getOb('plugins').listPlugins(
                              IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                {'login_portal_type': ('ERP5 Login', 'Certificate Login'),
                 'external_login': login}) is not None:
        self.fail(
           "Plugin %s should not have authenticated '%s' with password '%s'" %
           (plugin_name, login, password))

class TestSlapOSComputeNodeSecurity(TestSlapOSSecurityMixin):

  def test_active(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId('Compute Node')
    reference = self._generateRandomUniqueReference('Compute Node')

    project = self.addProject()

    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node', reference=reference, follow_up_value=project)
    compute_node.setUserId(user_id)
    compute_node.validate()
    compute_node.newContent(portal_type=login_portal_type,
                      reference=reference).validate()

    self.tic()

    self._assertUserExists(user_id, reference, None)

    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['R-COMPUTER'],
      user.getGroups())

  def test_inactive(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId('Compute Node')
    reference = self._generateRandomUniqueReference('Compute Node')

    compute_node = self.portal.compute_node_module.newContent(
      portal_type='Compute Node', reference=reference)
    compute_node.setUserId(user_id)
    compute_node.newContent(portal_type=login_portal_type,
                      reference=reference)
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)

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
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['R-INSTANCE'],
      user.getGroups())

    self.login()
    subscription_reference = self._generateRandomUniqueReference(
        'Instance Tree')
    subscription = self.portal.instance_tree_module.newContent(
        portal_type='Instance Tree',
        reference=subscription_reference)
    subscription.validate()
    instance.setSpecialise(subscription.getRelativeUrl())
    self.tic()

    # clear cache in order to reset calculation
    self.portal.portal_caches.clearAllCache()
    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['R-INSTANCE', subscription_reference],
      user.getGroups())

    # check project security group
    self.login()
    project = self.addProject()
    instance.setFollowUpValue(project)
    self.tic()

    # clear cache in order to reset calculation
    self.portal.portal_caches.clearAllCache()
    self.login(user_id)
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['R-INSTANCE', subscription_reference,
                        project.getReference(),
                        '%s_R-INSTANCE' % project.getReference()],
      user.getGroups())

  def test_inactive(self, login_portal_type="Certificate Login"):
    user_id = self._generateRandomUniqueUserId(self.portal_type)
    reference = self._generateRandomUniqueReference(self.portal_type)

    instance = self.portal.getDefaultModule(portal_type=self.portal_type)\
      .newContent(portal_type=self.portal_type, reference=reference)
    instance.setUserId(user_id)
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)

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
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet([], user.getGroups())


    # add to group category
    self.login()
    person.newContent(portal_type='Assignment', group='company').open()
    self.tic()

    self.tic()
    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet([], user.getGroups())

    # add to role category
    self.login()
    person.newContent(portal_type='Assignment', role='member').open()
    self.tic()

    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet([], user.getGroups())

    # add to function category
    self.login()
    person.newContent(portal_type='Assignment', function='accounting/manager').open()
    self.tic()

    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['F-ACCMAN', 'F-ACCOUNTING*', 'F-ACCMAN*'],
                       user.getGroups())

    # add project
    self.login()
    project = self.addProject()
    person.newContent(portal_type='Assignment',
      destination_project_value=project).open()
    self.tic()

    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['F-ACCMAN', 'F-ACCOUNTING*', 'F-ACCMAN*',
                        project.getReference()], user.getGroups())

    # add project and function
    self.login()
    project2 = self.addProject()
    person.newContent(portal_type='Assignment',
      destination_project_value=project2, function='production/manager').open()
    self.tic()

    self.portal.portal_caches.clearAllCache()
    self.login(person.getUserId())
    user = getSecurityManager().getUser()
    self.assertIn('Authenticated', user.getRoles())
    self.assertSameSet(['F-ACCMAN', 'F-ACCOUNTING*', 'F-ACCMAN*',
                        project.getReference(),
                        'F-PRODMAN', 'F-PRODUCTION*', 'F-PRODMAN*',
                        project2.getReference(),
                        '%s_F-PRODMAN' % project2.getReference()], user.getGroups())


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

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSComputeNodeSecurity))
  suite.addTest(unittest.makeSuite(TestSlapOSSoftwareInstanceSecurity))
  suite.addTest(unittest.makeSuite(TestSlapOSPersonSecurity))
  return suite
