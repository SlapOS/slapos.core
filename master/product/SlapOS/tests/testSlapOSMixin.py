# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Vifib SA and Contributors. All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly adviced to contract a Free Software
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
##############################################################################

import random
import transaction
import unittest
from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
from Products.ERP5Type.Utils import convertToUpperCase
import os
import glob
import shutil
from AccessControl.SecurityManagement import getSecurityManager, \
    setSecurityManager
from App.config import getConfiguration

config = getConfiguration()

class testSlapOSMixin(ERP5TypeTestCase):

  abort_transaction = 0

  def clearCache(self):
    self.portal.portal_caches.clearAllCache()
    self.portal.portal_workflow.refreshWorklistCache()

  def createAlarmStep(self):
    def makeCallAlarm(alarm):
      def callAlarm(*args, **kwargs):
        sm = getSecurityManager()
        self.login()
        try:
          alarm.activeSense(params=kwargs)
          self.commit()
        finally:
          setSecurityManager(sm)
      return callAlarm
    for alarm in self.portal.portal_alarms.contentValues():
      if alarm.isEnabled():
        setattr(self, 'stepCall' + convertToUpperCase(alarm.getId()) \
          + 'Alarm', makeCallAlarm(alarm))

  def createCertificateAuthorityFile(self):
    """Sets up portal_certificate_authority"""

    if 'TEST_CA_PATH' not in os.environ:
      return

    ca_path = os.path.join(os.environ['TEST_CA_PATH'],
                           self.__class__.__name__)

    if os.path.exists(ca_path):
      shutil.rmtree(ca_path)

    os.mkdir(ca_path)
    os.mkdir(os.path.join(ca_path, 'private'))
    os.mkdir(os.path.join(ca_path, 'crl'))
    os.mkdir(os.path.join(ca_path, 'certs'))
    os.mkdir(os.path.join(ca_path, 'requests'))
    os.mkdir(os.path.join(ca_path, 'newcerts'))

    original_openssl_cnf = open(
      os.path.join(os.environ['TEST_CA_PATH'], 'openssl.cnf'), "r").read()

    openssl_cnf_with_updated_path = original_openssl_cnf.replace(
            os.environ['TEST_CA_PATH'], ca_path)

    # SlapOS Master requires unique subjects
    openssl_cnf = openssl_cnf_with_updated_path.replace(
            "unique_subject  = no", "unique_subject  = yes")

    with open(os.path.join(ca_path, 'openssl.cnf'), "w") as f:
      f.write(openssl_cnf)

    shutil.copy(os.path.join(os.environ['TEST_CA_PATH'], 'cacert.pem'),
            os.path.join(ca_path, 'cacert.pem'))

    shutil.copy(os.path.join(os.environ['TEST_CA_PATH'], 'private', 'cakey.pem'),
            os.path.join(ca_path, 'private', 'cakey.pem'))

    # reset test CA to have it always count from 0
    open(os.path.join(ca_path, 'serial'), 'w').write('01')
    open(os.path.join(ca_path, 'crlnumber'), 'w').write('01')
    open(os.path.join(ca_path, 'index.txt'), 'w').write('')
    private_list = glob.glob('%s/*.key' % os.path.join(ca_path, 'private'))
    for private in private_list:
      os.remove(private)

    crl_list = glob.glob('%s/*' % os.path.join(ca_path, 'crl'))
    for crl in crl_list:
      os.remove(crl)

    certs_list = glob.glob('%s/*' % os.path.join(ca_path, 'certs'))
    for cert in certs_list:
      os.remove(cert)

    newcerts_list = glob.glob('%s/*' % os.path.join(ca_path, 'newcerts'))
    for newcert in newcerts_list:
      os.remove(newcert)

    self.portal.portal_certificate_authority.manage_editCertificateAuthorityTool(
      certificate_authority_path=ca_path)

  def isLiveTest(self):
    #return 'ERP5TypeLiveTestCase' in [q.__name__ for q in self.__class__.mro()]
    # XXX - What is the better way to know if we are in live test mode ?
    return not os.environ.has_key('TEST_CA_PATH')

  def beforeTearDown(self):
    if self.abort_transaction:
      transaction.abort()

  def setUpOnce(self):
    self.commit()
    self.portal.portal_templates.updateRepositoryBusinessTemplateList(
       repository_list=self.portal.portal_templates.getRepositoryList())
    self.commit()
    self.launchConfigurator()

  def afterSetUp(self):
    self.login()
    self.createAlarmStep()
    self.portal.email_from_address = 'romain@nexedi.com'
    self.portal.email_to_address = 'romain@nexedi.com'


    if getattr(self.portal.portal_caches, 'erp5_site_global_id', None):
      # we are not on live test so multiple tests can run in parallel
      # so ensure that each start tests from scratch
      self.portal.portal_caches.erp5_site_global_id = '%s' % random.random()
      self.portal.portal_caches._p_changed = 1

    if self.isLiveTest():
      return
    self.createCertificateAuthorityFile() 
    self.commit()
    self.portal.portal_caches.updateCache()

  def getBusinessConfiguration(self):
    return self.portal.business_configuration_module[\
                          "slapos_master_configuration_workflow"]

  def launchConfigurator(self):
    self.logMessage('SlapOS launchConfigurator ...\n')
    self.login()
    # Create new Configuration 
    business_configuration  = self.getBusinessConfiguration()

    response_dict = {}
    while response_dict.get("command", "next") != "install":
      response_dict = self.portal.portal_configurator._next(
                            business_configuration, {})

    self.tic() 
    self.portal.portal_configurator.startInstallation(
                 business_configuration,REQUEST=self.portal.REQUEST)

    self.portal.portal_types.resetDynamicDocumentsOnceAtTransactionBoundary()
    # Delay 4 hours
    self.tic(verbose=True, delay=4 * 60 * 60)

    # Set post upgrade configurations for the tests
    preference_tool = self.portal.portal_preferences.portal_preferences
    preference_tool.slapos_default_system_preference.setPreferredHateoasUrl("http://dummy/")
    preference_tool.slapos_default_system_preference.setPreferredAuthenticationPolicyEnabled(True)

    self.tic()
    self.clearCache()

  def getExpectedBusinessTemplateInstalledAfterConfiguration(self):
    return [
      'erp5_core',
      'erp5_xhtml_style',
      'erp5_property_sheets',
      'erp5_mysql_innodb_catalog',
      'erp5_upgrader',
      'slapos_upgrader',
      'erp5_full_text_mroonga_catalog',
      'erp5_core_proxy_field_legacy',
      'erp5_base',
      'erp5_administration',
      'erp5_configurator',
      'slapos_configurator',
      'erp5_simulation',
      'erp5_pdm',
      'erp5_trade',
      'erp5_item',
      'erp5_ingestion_mysql_innodb_catalog',
      'erp5_ingestion',
      'erp5_crm',
      'erp5_forge',
      'erp5_system_event',
      'erp5_secure_payment',
      'erp5_security_uid_innodb_catalog',
      'erp5_payzen_secure_payment',
      'erp5_wechat_secure_payment',
      'erp5_ooo_import',
      'erp5_odt_style',
      'erp5_ods_style',
      'erp5_knowledge_pad',
      'erp5_web',
      'erp5_jquery',
      'erp5_jquery_plugin_colorpicker',
      'erp5_jquery_plugin_elastic',
      'erp5_jquery_plugin_jqchart',
      'erp5_jquery_plugin_mbmenu',
      'erp5_jquery_ui',
      'erp5_jquery_plugin_sheet',
      'erp5_jquery_sheet_editor',
      'erp5_deferred_style',
      'erp5_dhtml_style',
      'erp5_rss_style',
      'erp5_dms',
      'erp5_content_translation',
      'erp5_software_pdm',
      'erp5_svg_editor',
      'erp5_syncml',
      'erp5_immobilisation',
      'erp5_computer_immobilisation',
      'erp5_open_trade',
      'erp5_accounting',
      'erp5_commerce',
      'erp5_credential',
      'erp5_km',
      'erp5_web_download_theme',
      'erp5_web_shacache',
      'erp5_data_set',
      'erp5_web_shadir',
      'erp5_invoicing',
      'erp5_simplified_invoicing',
      'erp5_credential_oauth2',
      'erp5_accounting_l10n_fr',
      'erp5_accounting_l10n_ifrs',
      'erp5_code_mirror',
      'erp5_font',
      'erp5_hal_json_style',
      'erp5_l10n_fr',
      'erp5_l10n_ja',
      'erp5_l10n_zh',
      'erp5_monaco_editor',
      'erp5_json_editor',
      'erp5_movement_table_catalog',
      'erp5_oauth',
      'erp5_bearer_token',
      'erp5_oauth_facebook_login',
      'erp5_oauth_google_login',
      'erp5_web_renderjs_ui',
      'erp5_web_service',
      'erp5_oauth2_resource',
      'erp5_tiosafe_core',
      'erp5_graph_editor',
      'slapos_l10n_zh',
      'erp5_certificate_authority',
      'erp5_access_token',
      'erp5_project',
      'erp5_run_my_doc',
      'erp5_slapos_tutorial',
      'erp5_slapos_tutorial_data',	
      'erp5_slideshow_style',
      'erp5_authentication_policy',
      'erp5_multimedia',
      'erp5_notebook',
      'erp5_officejs',
      'erp5_corporate_identity',
      'erp5_big_file',
      'erp5_data_notebook',
      'erp5_wendelin',
      'erp5_development_wizard',
      'erp5_smart_assistant',
      'erp5_interaction_drop',
      'slapos_mysql_innodb_catalog',
      'slapos_cloud',
      'slapos_slap_tool',
      'slapos_category',
      'slapos_rss_style',
      'slapos_pdm',
      'slapos_crm',
      'slapos_accounting',
      'slapos_payzen',
      'slapos_wechat',
      'slapos_web_deploy',
      'slapos_subscription_request',
      'slapos_abyss',
      'slapos_jio',
      'slapos_erp5',
    ]
 
  def getBusinessTemplateList(self):
    """
    Install the business templates.
    """
    result = [
      'erp5_full_text_mroonga_catalog',
      'erp5_core_proxy_field_legacy',
      'erp5_base',
      'erp5_simulation',
      'erp5_accounting',
      'erp5_configurator',
      'slapos_configurator',
    ]
    if int(os.environ.get('erp5_load_data_fs', 0)):
      result.extend(
        self.getExpectedBusinessTemplateInstalledAfterConfiguration())
    return result

  def _getSiteCreationParameterDict(self):
    kw = super(testSlapOSMixin, self)._getSiteCreationParameterDict()
    bt5_repository_path_list = self._getBusinessRepositoryPathList(
                ['erp5_core', 'erp5_slapos_tutorial', 'erp5_notebook', 'erp5_wendelin'] + list(self.getBusinessTemplateList()))
    kw["bt5_repository_url"] = " ".join(bt5_repository_path_list)
    return kw

class TestSlapOSDummy(testSlapOSMixin):
  run_all_test = 1
  def test(self):
    """Dummy test in order to fire up Business Template testing"""
    bt5_list = self.portal.portal_templates.getInstalledBusinessTemplateTitleList()
    self.assertTrue('slapos_erp5' in bt5_list, bt5_list)

  def getTitle(self):
    return "Dummy tests in order to have tests from BT5 run"

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestSlapOSDummy))
  return suite
