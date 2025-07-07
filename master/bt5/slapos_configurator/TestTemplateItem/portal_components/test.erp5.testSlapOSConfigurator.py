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
  def testConfiguredModuleGeneratorIDViaConstraint(self):
    """ Make sure Generator ID is well configured, in this
        case we trust on promise outcome."""
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])

    self.portal.person_module.setIdGenerator("_Id_fake")
    self.assertNotEqual(self.portal.portal_ids.checkConsistency(), [])
    self.portal.portal_ids.fixConsistency()
    self.assertEqual(self.portal.portal_ids.checkConsistency(), [])
    self.assertEqual(self.portal.person_module.getIdGenerator(),
                        "_generatePerDayNodeNumberId")

  def testConfiguredShacacheWebSite(self):
    """ Make sure Shacache WebSite is setuped by Alarm
        case we trust on promise outcome, this checks:
        WebSiteModule_checkShacacheConstraint """
    self.assertEqual(self.portal.web_site_module.checkConsistency(), [])

  def testConfiguredCacheViaConstraint(self):
    """ Make sure Volitile and Persistent Cache was configured well,
        invoking the consistency to check """
    self.assertEqual(self.portal.portal_memcached.checkConsistency(), [])

  def testConfiguredConversionServerViaConstraint(self):
    """ Make sure Conversion Server was configured well,
        invoking checkConsistency """
    pref_tool = self.portal.portal_preferences
    self.portal.portal_preferences.fixConsistency()
    consistency_list = pref_tool.checkConsistency()
    self.assertEqual(len(consistency_list), 1)
    self.assertEqual(str(consistency_list[0].message), 'The System Preference subscription assignment should have a destination_project')

    # Check if configuration is properly set:
    consistency_list = pref_tool.slapos_default_system_preference.SystemPreference_checkSystemPreferenceConsistency()
    self.assertEqual(len(consistency_list), 1)
    self.assertEqual(str(consistency_list[0]), 'The System Preference subscription assignment should have a destination_project')

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

  def test_SystemPreference_checkConversionServerConsistency(self):
    """ Make sure Conversion Server (Cloudooo) is
        well configured."""
    # set preference
    preference_tool = self.portal.portal_preferences
    conversion_url = ["https://cloudooo.erp5.net/",
                      "https://cloudooo1.erp5.net/"]
    self.assertSameSet(preference_tool.getPreferredDocumentConversionServerUrlList(), conversion_url)

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

  def test_TemplateTool_checkSlapOSPASConsistency(self):
    """ Ensure that PAS is configured after the configuration """
    self.assertEqual(self.portal.portal_templates.TemplateTool_checkSlapOSPASConsistency(),
      [])
    self.assertEqual(self.portal.portal_templates.TemplateTool_checkSlapOSPASConsistency(),
      [])
    

  def testInteractionDropped(self):
    """ Make sure that no portal type uses interaction workflow for simulation """
    for pt in self.portal.portal_types.objectValues():
      for dropped_workflow in [
            "delivery_movement_simulation_interaction_workflow",
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

  def test_Module_checkSlapOSModuleIdGeneratorConsistency(self):
    """ Ensure the Constraint sets appropriate id generator on all modules.
    """
    module_list = [module.getId() for module in self.portal.objectValues() 
                     if getattr(module, "getIdGenerator", None) is not None and \
                                        module.getIdGenerator() == "_generatePerDayNodeNumberId"]
    expected_module_list = [
       'access_token_module',
       'account_module',
       'accounting_module',
       'allocation_supply_module',
       'business_configuration_module',
       'business_process_module',
       'campaign_module',
       'component_module',
       'computer_model_module',
       'compute_node_module',
       'computer_module',
       'compute_node_module',
       'computer_network_module',
       'consumption_delivery_module',
       'consumption_document_module',
       'consumption_supply_module',
       'credential_recovery_module',
       'credential_request_module',
       'credential_update_module',
       'currency_module',
       'data_set_module',
       'delivery_node_module',
       'document_ingestion_module',
       'document_module',
       'event_module',
       'external_source_module',
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
       'notebook_module',
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
       'subscription_change_request_module',
       'subscription_request_module',
       'support_request_module',
       'system_event_module',
       'task_module',
       'task_report_module',
       'test_page_module',
       'transformation_module',
       'upgrade_decision_module',
       'web_page_module',
       'web_site_module',
       'data_descriptor_module',
       'data_ingestion_batch_module',
       'data_aggregation_unit_module',
       'data_configuration_module',
       'data_order_module',
       'sensor_module',
       'data_event_module',
       'data_ingestion_module',
       'data_stream_module',
       'data_transformation_module',
       'progress_indicator_module',
       'data_acquisition_unit_module',
       'data_operation_module',
       'device_configuration_module',
       'data_license_module',
       'data_notebook_module',
       'data_release_module',
       'data_supply_module',
       'data_product_module',
       'big_file_module',
       'data_analysis_module',
       'data_array_module',
       'data_mapping_module'
    ]
    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_module_list.extend(self._custom_expected_module_list)

    self.assertSameSet(module_list, expected_module_list)

    self.assertEqual(self.portal.portal_simulation.getIdGenerator(), "_generatePerDayNodeNumberId")    
    self.assertEqual(self.portal.portal_activities.getIdGenerator(), "_generatePerDayNodeNumberId")

  def testConfiguredBusinessTemplateList(self):
    """ Make sure Installed business Templates are
        what it is expected.  """

    expected_business_template_list = self.getExpectedBusinessTemplateInstalledAfterConfiguration()

    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_business_template_list.extend(self._custom_additional_bt5_list)

    self.assertSameSet(expected_business_template_list,
      self.portal.portal_templates.getInstalledBusinessTemplateTitleList())

  def testConfiguredExpectedBusinessTemplateDependencyList(self):
    """ Make sure TemplateTool_getSlapOSMasterBusinessTemplateList dependency resolution
        provides the expected bt5 list. """

    expected_business_template_list = self.getExpectedBusinessTemplateInstalledAfterConfiguration()

    # If mixin contains a custom definition that introduce new business templated from
    # the project scope, them include it on expected list.
    expected_business_template_list.extend(self._custom_additional_bt5_list)

    bt5_to_resolve, _, _ = self.portal.portal_templates.TemplateTool_getSlapOSMasterBusinessTemplateList()

    bt5_list = [i[1] for i in self.portal.portal_templates.resolveBusinessTemplateListDependency(
        template_title_list=bt5_to_resolve,
        with_test_dependency_list=True)]
    self.assertSameSet(expected_business_template_list, bt5_list)