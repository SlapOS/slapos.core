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
from erp5.component.test.testSlapOSCloudSecurityGroup import TestSlapOSSecurityMixin

class TestSlapOSShadowPerson(TestSlapOSSecurityMixin):
  def test_active(self):
    reference = self._generateRandomUniqueReference('Person')
    user_id = self._generateRandomUniqueUserId('Person')
    shadow_user_id = 'SHADOW-%s' % user_id

    person = self.portal.person_module.newContent(
      portal_type='Person')
    person.setUserId(user_id)
    person.newContent(portal_type='Assignment').open()

    password = person.Person_generatePassword()
    person.newContent(portal_type='ERP5 Login',
          reference=reference, password=password).validate()
    self.tic()

    self._assertUserExists(user_id, reference, password)

    # XXX shadow user cannot login himself.
    self._assertUserExists(shadow_user_id, reference, None)

    self.login(shadow_user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-SHADOW-PERSON', 'SHADOW-%s' % user_id],
      user.getGroups())

  def test_inactive(self):
    password = str(random.random())
    reference = self._generateRandomUniqueReference('Person')
    user_id = self._generateRandomUniqueUserId('Person')

    shadow_user_id = 'SHADOW-%s' % user_id
    person = self.portal.person_module.newContent(
      portal_type='Person')
    person.setUserId(user_id)

    self.tic()

    self._assertUserDoesNotExists(user_id, reference, password)
    self._assertUserDoesNotExists(shadow_user_id, reference, None)

class TestSlapOSShadowComputer(TestSlapOSSecurityMixin):
  def test_active(self):
    reference = self._generateRandomUniqueReference('Computer')
    user_id = self._generateRandomUniqueUserId('Computer')

    shadow_user_id = 'SHADOW-%s' % user_id

    computer = self.portal.computer_module.newContent(portal_type='Computer',
      reference=reference)
    computer.setUserId(user_id)

    computer.newContent(portal_type='ERP5 Login',
          reference=reference).validate()

    computer.validate()
    self.tic()

    self._assertUserExists(user_id, reference, None)
    self._assertUserExists(shadow_user_id, reference, None)

    self.login(shadow_user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-SHADOW-COMPUTER', 'SHADOW-%s' % user_id],
      user.getGroups())

  def test_inactive(self):
    reference = self._generateRandomUniqueReference('Computer')
    user_id = self._generateRandomUniqueUserId('Computer')

    shadow_reference = 'SHADOW-%s' % reference

    computer = self.portal.computer_module.newContent(portal_type='Computer',
      reference=reference)
    computer.setUserId(user_id)

    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)
    self._assertUserDoesNotExists(user_id, shadow_reference, None)

class TestSlapOSShadowSoftwareInstance(TestSlapOSSecurityMixin):
  portal_type = 'Software Instance'
  def test_active(self):
    reference = self._generateRandomUniqueReference(self.portal_type)
    user_id = self._generateRandomUniqueUserId(self.portal_type)

    shadow_user_id = 'SHADOW-%s' % user_id

    instance = self.portal.getDefaultModule(portal_type=self.portal_type)\
      .newContent(portal_type=self.portal_type, reference=reference)
    instance.setUserId(user_id)
    instance.newContent(portal_type='ERP5 Login',
          reference=reference).validate()
    instance.validate()
    self.tic()

    self._assertUserExists(user_id, reference, None)
    self._assertUserExists(shadow_user_id, reference, None)

    self.login(shadow_user_id)
    user = getSecurityManager().getUser()
    self.assertTrue('Authenticated' in user.getRoles())
    self.assertSameSet(['R-SHADOW-SOFTWAREINSTANCE', 'SHADOW-%s' % user_id],
      user.getGroups())

  def test_inactive(self):
    reference = self._generateRandomUniqueReference(self.portal_type)
    user_id = self._generateRandomUniqueUserId(self.portal_type)

    shadow_reference = 'SHADOW-%s' % reference

    instance = self.portal.getDefaultModule(portal_type=self.portal_type)\
      .newContent(portal_type=self.portal_type, reference=reference)
    instance.setUserId(user_id)
    self.tic()

    self._assertUserDoesNotExists(user_id, reference, None)
    self._assertUserDoesNotExists(user_id, shadow_reference, None)

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSShadowPerson))
  suite.addTest(unittest.makeSuite(TestSlapOSShadowComputer))
  suite.addTest(unittest.makeSuite(TestSlapOSShadowSoftwareInstance))
  return suite
