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
  SlapOSTestCaseMixin
import os

class TestSlapOSConfigurator(SlapOSTestCaseMixin):

  maxDiff = None
  def bootstrapSite(self):
    SlapOSTestCaseMixin.bootstrapSite(self)
    self.getBusinessConfiguration().BusinessConfiguration_invokeSlapOSMasterPromiseAlarmList()
    self.tic()

  def testConfiguredModuleGeneratorIDViaConstraint(self):
    """ Make sure Generator ID is well configured, in this
        case we trust on promise outcome."""
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])

    self.portal.person_module.setIdGenerator("_Id_fake")
    self.assertNotEqual(self.portal.portal_ids.checkConsistency(), [])
    self.portal.portal_ids.fixConsistency()
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])
    self.assertEqual(self.portal.person_module.getIdGenerator(),
                        "_generatePerDayId")

  def testConfiguredShacacheWebSite(self):
    """ Make sure Shacache WebSite is setuped by Alarm
        case we trust on promise outcome."""
    self.assertEqual(self.portal.web_site_module.checkConsistency(), [])

  def testConfiguredCacheViaConstraint(self):
    """ Make sure Volitile and Persistent Cache was configured well,
        invoking the consistency to check """
    self.assertEqual(self.portal.portal_memcached.checkConsistency(), [])

  def testConfiguredConversionServerViaConstraint(self):
    """ Make sure Conversion Server was configured well,
        invoking checkConsistency """
    self.assertEqual(self.portal.portal_preferences.checkConsistency(), [])

  def testConfiguredCertificateAuthoringConstraint(self):
    """Make sure Certificate Authoring was configured well,
       invoking checkConsistency.

       Make sure PAS is well configured."""
    # The certificate_authority_path is modified by the setup, invoke
    # fixConsistency here to restore it like the originally expected.    
    self.portal.portal_certificate_authority.fixConsistency()

    self.assertEqual(self.portal.portal_certificate_authority.checkConsistency(), [])

  def testConfiguredTemplateToolViaConstraint(self):
    """ Make sure Template Tool Repositories was configured well,
        invoking checkConsistency """
    self.assertEqual(
        [ i for i in self.portal.portal_templates.checkConsistency()
                     if not ("(reinstall)" in i.message or "Update translation table" in i.message)], [])

  def testConfiguredModuleBusinessApplication(self):
    """ Make sure that Modules has proper business_application set
        by TemplateToolBusinessApplicationModuleCategoryConstraint constraint """
    
    self.assertEqual([],
      self.portal.portal_templates.TemplateTool_checkBusinessApplicationToModuleConsistency())

  def testConfiguredVolatileCache(self):
    """  Make sure Memcached is configured
    """
    if self.isLiveTest():
      # This test is redundant with testConfiguredVolatileCacheViaPromise
      # and it is only aims to verify if test environment is behaving as
      # expected, nothing else, and if alamrs were invoked.
      return
    from Products.ERP5Type.tests.ERP5TypeTestCase import \
                                         _getVolatileMemcachedServerDict

    memcached_tool = self.getPortal().portal_memcached
    connection_dict = _getVolatileMemcachedServerDict()
    url_string = 'erp5-memcached-volatile:%(port)s' % connection_dict
    self.assertEqual(memcached_tool.default_memcached_plugin.getUrlString(),
                      url_string)

  def testConfiguredPersistentCache(self):
    """ Make sure Kumofs is configured
    """
    if self.isLiveTest():
      # This test is redundant with testConfiguredVolatileCacheViaPromise
      # and it is only aims to verify if test environment is behaving as
      # expected, nothing else, and if alamrs were invoked.
      return

    from Products.ERP5Type.tests.ERP5TypeTestCase import\
            _getPersistentMemcachedServerDict
    memcached_tool = self.getPortal().portal_memcached
    connection_dict = _getPersistentMemcachedServerDict()
    url_string = 'erp5-memcached-persistent:%(port)s' % connection_dict
    self.assertEqual(memcached_tool.persistent_memcached_plugin.getUrlString(),
                      url_string)

  def testConfiguredConversionServer(self):
    """ Make sure Conversion Server (Cloudooo) is
        well configured """
    if self.isLiveTest():
      # This test is redundant with testConfiguredConversionServerViaConstraint
      # and it is only aims to verify if test environment is behaving as
      # expected, nothing else, and if alamrs were invoked.
      return

    # set preference
    preference_tool = self.portal.portal_preferences
    conversion_url = "https://cloudooo.erp5.net"
    self.assertEqual(preference_tool.getPreferredDocumentConversionServerUrl(), conversion_url)

  def testConfiguredCertificateAuthoring(self):
    """ Make sure Certificate Authoting is
        well configured. """

    if self.isLiveTest():
      # This test is redundant with testConfiguredVolatileCacheViaPromise
      # and it is only aims to verify if test environment is behaving as
      # expected, nothing else, and if alamrs were invoked.
      return

    # The certificate_authority_path is modified by the setup, invoke
    # fixConsistency here to restore it like the originally expected.
    self.portal.portal_certificate_authority.fixConsistency()

    self.assertTrue(self.portal.hasObject('portal_certificate_authority'))
    self.assertEqual(os.environ['TEST_CA_PATH'],
          self.portal.portal_certificate_authority.certificate_authority_path)

  def testAlarmIsSubscribed(self):
    """ Make sure portal_alarms is subscribed. """
    self.assertTrue(self.portal.portal_alarms.isSubscribed())

  def testInteractionDropped(self):
    """ Make sure that no portal type uses interaction workflow for simulation """
    for pt in self.portal.portal_types.objectValues():
      for dropped_workflow in ["delivery_movement_simulation_interaction_workflow",
            "delivery_simulation_interaction_workflow",
            "open_order_simulation_interaction_workflow",
            "open_order_path_simulation_interaction_workflow",
            "container_interaction_workflow",
            "transformation_interaction_workflow",
            "trade_model_line_interaction_workflow"]:
        self.assertNotIn(dropped_workflow,
              pt.getTypeWorkflowList(),
              "Workflow %s still present on %s Portal Type (%s)" % \
                      (dropped_workflow, pt, pt.getTypeWorkflowList()))

  def testModuleHasIdGeneratorByDay(self):
    """ Ensure the Constraint sets appropriate id generator on all modules.
    """
    module_list = [module.getId() for module in self.portal.objectValues() 
                     if getattr(module, "getIdGenerator", None) is not None and \
                                        module.getIdGenerator() == "_generatePerDayId"]
    expected_module_list = [
       'access_token_module',
       'account_module',
       'accounting_module',
       'bug_module',
       'business_configuration_module',
       'business_process_module',
       'campaign_module',
       'component_module',
       'computer_model_module',
       'compute_node_module',
       'computer_module',
       'compute_node_module',
       'computer_network_module',
       'consumption_document_module',
       'credential_recovery_module',
       'credential_request_module',
       'credential_update_module',
       'currency_module',
       'cloud_contract_module',
       'data_set_module',
       'delivery_node_module',
       'document_ingestion_module',
       'document_module',
       'event_module',
       'external_source_module',
       'glossary_module',
       'hosting_subscription_module',
       'instance_tree_module',
       'image_module',
       'immobilisation_module',
       'implicit_item_movement_module',
       'incident_response_module',
       'internal_order_module',
       'internal_packing_list_module',
       'internal_supply_module',
       'internal_trade_condition_module',
       'inventory_module',
       'inventory_report_module',
       'invitation_token_module',
       'item_module',
       'knowledge_pad_module',
       'meeting_module',
       'notification_message_module',
       'open_internal_order_module',
       'open_purchase_order_module',
       'open_sale_order_module',
       'organisation_module',
       'person_module',
       'portal_activities',
       'portal_simulation',
       'product_module',
       'project_module',
       'purchase_order_module',
       'purchase_packing_list_module',
       'purchase_supply_module',
       'purchase_trade_condition_module',
       'quantity_unit_conversion_module',
       'query_module',
       'regularisation_request_module',
       'requirement_module',
       'returned_purchase_order_module',
       'returned_purchase_packing_list_module',
       'returned_sale_order_module',
       'returned_sale_packing_list_module',
       'review_module',
       'sale_opportunity_module',
       'sale_order_module',
       'sale_packing_list_module',
       'sale_supply_module',
       'sale_trade_condition_module',
       'service_module',
       'service_report_module',
       'software_installation_module',
       'software_instance_module',
       'software_licence_module',
       'software_product_module',
       'software_publication_module',
       'software_release_module',
       'subscription_condition_module',
       'subscription_request_module',
       'support_request_module',
       'system_event_module',
       'task_module',
       'task_report_module',
       'test_page_module',
       'transformation_module',
       'trial_condition_module',
       'trial_request_module',
       'upgrade_decision_module',
       'web_page_module',
       'web_site_module',
    ]
    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_module_list.extend(self._custom_expected_module_list)

    self.assertSameSet(module_list, expected_module_list)


  def testConfiguredBusinessTemplateList(self):
    """ Make sure Installed business Templates are
        what it is expected.  """

    expected_business_template_list = [
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
      'erp5_tiosafe_core',
      'erp5_item',
      'erp5_forge',
      'erp5_ingestion_mysql_innodb_catalog',
      'erp5_ingestion',
      'erp5_crm',
      'erp5_system_event',
      'erp5_secure_payment',
      'erp5_security_uid_innodb_catalog',
      'erp5_payzen_secure_payment',
      'erp5_wechat_secure_payment',
      'erp5_ooo_import',
      'erp5_odt_style',
      'erp5_ods_style',
      'erp5_jquery',
      'erp5_jquery_plugin_colorpicker',
      'erp5_jquery_plugin_elastic',
      'erp5_jquery_plugin_jqchart',
      'erp5_jquery_plugin_mbmenu',
      'erp5_jquery_plugin_sheet',
      'erp5_jquery_sheet_editor',
      'erp5_jquery_ui',
      'erp5_deferred_style',
      'erp5_dhtml_style',
      'erp5_knowledge_pad',
      'erp5_web',
      'erp5_rss_style',
      'erp5_dms',
      'erp5_content_translation',
      'erp5_software_pdm',
      'erp5_svg_editor',
      'erp5_syncml',
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
      'erp5_immobilisation',
      'erp5_l10n_fr',
      'erp5_l10n_ja',
      'erp5_l10n_zh',
      'erp5_monaco_editor',
      'erp5_movement_table_catalog',
      'erp5_web_renderjs_ui',
      'erp5_web_service',
      'slapos_ecoallocation',
      'slapos_jio',
      'slapos_l10n_zh',
      'slapos_subscription_request',
      'erp5_bearer_token',
      'erp5_certificate_authority',
      'erp5_access_token',
      'erp5_project',
      'erp5_oauth',
      'erp5_oauth_facebook_login',
      'erp5_oauth_google_login',
      'erp5_run_my_doc',
      'erp5_slapos_tutorial',
      'erp5_slapos_tutorial_data',	
      'erp5_slideshow_style',
      'erp5_authentication_policy',
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
      'slapos_web',
      'slapos_web_deploy',
      'slapos_erp5',
    ]

    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_business_template_list.extend(self._custom_additional_bt5_list)

    self.assertSameSet(expected_business_template_list,
      self.portal.portal_templates.getInstalledBusinessTemplateTitleList())
