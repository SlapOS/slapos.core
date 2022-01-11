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
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSAuthenticationPolicyL(SlapOSTestCaseMixin):

  def afterSetUp(self):
    SlapOSTestCaseMixin.afterSetUp(self)
    self.assertTrue(
      self.portal.portal_preferences.isAuthenticationPolicyEnabled())
    self.system_preference = self.portal.portal_preferences.getActiveSystemPreference()
    self.system_preference.setPreferredMaxPasswordLifetimeDuration(0) 

  def _clearCache(self):
    self.portal.portal_caches.clearCache(
      cache_factory_list=('erp5_content_short', # for authentication cache
                          ))
    self.tic()

  def _cleanUpLogin(self, login):
    self.portal.system_event_module.manage_delObjects(
      [x.getId() for x in self._getPasswordEventList(login)])

  def _getPasswordEventList(self, login):
    return [x.getObject() for x in self.portal.portal_catalog(
                                                 portal_type='Password Event',
                                                 default_destination_uid=login.getUid(),
                                                 sort_on=(('creation_date', 'DESC',),))]

  def _notifyLoginFailureAboveMaximum(self, login):
    login.notifyLoginFailure()
    for _ in range(self.portal.portal_preferences.getPreferredMaxAuthenticationFailure(1)):
      login.notifyLoginFailure()
    
    self._clearCache()

  def _makeLogin(self, document, portal_type):
    login = document.newContent(
        portal_type=portal_type,
        reference=document.getReference())
    login.validate()
    return login

  def _makeDummySoftwareInstance(self):
    software_instance = self.portal.software_instance_module\
        .newContent(portal_type="Software Instance")

    software_instance.edit(
        title=self.generateNewSoftwareTitle(),
        reference="TESTSI-%s" % self.generateNewId()
    )
    return software_instance

  def _test(self, document, login_portal_type):
    login = self._makeLogin(
      document=document,
      portal_type=login_portal_type)
     
    self._notifyLoginFailureAboveMaximum(login)
    self.assertFalse(login.isLoginBlocked())

    # Password should be ignored
    login.setPassword(document.Person_generatePassword())

    self._clearCache()
    self.tic()
    return login

  def _test_login_donot_block(self, document, login_portal_type):
    login = self._test(document, login_portal_type)
    self.assertFalse(login.isLoginBlocked())

  def _test_login_block_if_password_is_set(self, document, login_portal_type):
    login = self._test(document, login_portal_type)
    self.assertTrue(login.isLoginBlocked())

  def test_block_CertificateLogin_without_password_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_login_donot_block(
      document=person,
      login_portal_type="Certificate Login"
    )

  def test_block_CertificateLogin_without_password_on_compute_node(self):
    self._test_login_donot_block(
      document=self._makeComputeNode(self.addProject())[0],
      login_portal_type="Certificate Login")
  
  def test_block_CertificateLogin_without_password_on_software_instance(self):
    self._test_login_donot_block(
      document=self._makeDummySoftwareInstance(),
      login_portal_type="Certificate Login")

  def test_block_GoogleLogin_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_login_donot_block(
      document=person,
      login_portal_type="Google Login"
    )
  
  def test_block_FacebookLogin_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_login_donot_block(
      document=person,
      login_portal_type="Facebook Login"
    )

  def _test_expire(self, document, login_portal_type):
    request = self.app.REQUEST
    login = self._makeLogin(
      document=document,
      portal_type=login_portal_type)

    self._clearCache()
    self.assertFalse(login.isPasswordExpired())

    # set longer password validity interval
    self.system_preference.setPreferredMaxPasswordLifetimeDuration(0) 
    self._clearCache()
    self.assertFalse(login.isPasswordExpired())
    self.assertNotIn('is_user_account_password_expired', request)

    # test early warning password expire notification is detected
    self.system_preference.setPreferredPasswordLifetimeExpireWarningDuration(4*24) # password expire notification appear immediately
    self._clearCache()
    self.assertFalse(login.isPasswordExpired())
    self.assertNotIn('is_user_account_password_expired_expire_date', request)

    # test early warning password expire notification is detected
    self.system_preference.setPreferredPasswordLifetimeExpireWarningDuration(4*24-24) # password expire notification appear 3 days befor time
    self.tic()
    self._clearCache()
    self.assertFalse(login.isPasswordExpired())
    self.assertNotIn('is_user_account_password_expired_expire_date', request)
    return login

  def _test_expire_when_passoword_is_set(self, document, login_portal_type):
    login = self._test_expire(
      document=document,
      login_portal_type=login_portal_type
    )

    login.setPassword(document.Person_generatePassword())
    self.system_preference.setPreferredMaxPasswordLifetimeDuration(0)
    self._clearCache()
    self.assertTrue(login.isPasswordExpired())

  def _test_dont_expire_when_password_isnt_set(self, document, login_portal_type):
    login = self._test_expire(
      document=document,
      login_portal_type=login_portal_type
    )

    login.setPassword(document.Person_generatePassword())
    self.system_preference.setPreferredMaxPasswordLifetimeDuration(0)
    self._clearCache()
    self.assertFalse(login.isPasswordExpired())

  def test_expire_CertificateLogin_without_password_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_dont_expire_when_password_isnt_set(
      document=person,
      login_portal_type="Certificate Login"
    )

  def test_expire_CertificateLogin_without_password_on_compute_node(self):
    self._test_dont_expire_when_password_isnt_set(
      document=self._makeComputeNode(self.addProject())[0],
      login_portal_type="Certificate Login")
  
  def test_expire_CertificateLogin_without_password_on_software_instance(self):
    self._test_dont_expire_when_password_isnt_set(
      document=self._makeDummySoftwareInstance(),
      login_portal_type="Certificate Login")

  def test_expire_GoogleLogin_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_dont_expire_when_password_isnt_set(
      document=person,
      login_portal_type="Google Login"
    )
  
  def test_expire_FacebookLogin_on_person(self):
    person = self.makePerson(self.addProject(), user=0)
    person.edit(
      first_name="SOMENAME",
      last_name="LASTNAME"
    )
    self._test_dont_expire_when_password_isnt_set(
      document=person,
      login_portal_type="Facebook Login"
    )
