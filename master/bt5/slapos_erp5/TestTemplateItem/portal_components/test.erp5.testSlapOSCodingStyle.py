# -*- coding: utf8 -*-
##############################################################################
#
# Copyright (c) 2020 Nexedi SA and Contributors. All Rights Reserved.
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

import unittest
from Products.ERP5Type.tests.CodingStyleTestCase import CodingStyleTestCase
from Products.ERP5Type import CodingStyle

from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

def makeTestSlapOSCodingStyleTestCase(tested_business_template):
  class TestSlapOSCodingStyle(CodingStyleTestCase, SlapOSTestCaseMixin):
    """Runs CodingStyleTestCase checks on slapos business templates
    """
    def afterSetUp(self):
      CodingStyleTestCase.afterSetUp(self)
      CodingStyle.ignored_skin_id_set.update({
        'InstanceTree_viewConsumptionReport',
        'Person_viewResourceConsumptionReport'})

      CodingStyleTestCase.rebuild_business_template_ignored_path += """

      # Those preferences are changed after the installation, so we skip
      # to check re-export.
      slapos_cloud/PreferenceTemplateItem/portal_preferences/slapos_default_system_preference.xml
      slapos_cloud/PreferenceTemplateItem/portal_preferences/slapos_default_site_preference.xml

      # Since the sections can be overwriten on project context, keep it on ignore list.
      slapos_jio/PathTemplateItem/web_site_module/hostingjs/feed.xml
      slapos_jio/PathTemplateItem/web_site_module/hostingjs/feed/critical.xml
      slapos_jio/PathTemplateItem/web_site_module/hostingjs/feed/invoice.xml

      # WebSite is updated after the installation to re-generate the translation data.
      # This list should be reconsider later so we can keep information accurated.
      slapos_jio/PathTemplateItem/web_site_module/hostingjs.xml
      slapos_jio/PathTemplateItem/web_page_module/rjs_gadget_slapos_translation_data_js.js
      slapos_jio/PathTemplateItem/web_page_module/rjs_gadget_slapos_translation_data_js.xml
      slapos_jio/PathTemplateItem/web_site_module/renderjs_oss.xml

      # Modified by subprojects during tests
      slapos_crm/PathTemplateItem/sale_trade_condition_module/slapos_ticket_trade_condition.xml
      slapos_payzen/PathTemplateItem/portal_secure_payments/slapos_payzen_test.xml

      # Modified during the configuration
      slapos_configurator/PathTemplateItem/business_configuration_module/slapos_master_configuration_workflow.xml
      """

      CodingStyleTestCase.coverage_ignore_path_list = [
        'erp5_interaction_drop/InvoiceTransaction_postGeneration',
        'slapos_cloud/AlarmTool_checkComputeNodeMigrationConsistency',
        'slapos_cloud/AlarmTool_checkInstanceTreeMigrationConsistency',
        'slapos_cloud/AlarmTool_checkPredecessorToSuccessorMigrationConsistency',
        'slapos_cloud/ComputeNode_afterClone',
        'slapos_cloud/ComputeNode_applyComputerModel',
        'slapos_cloud/ComputeNode_getBusyComputePartitionList',
        'slapos_cloud/ComputeNode_getFreeComputePartitionCount',
        'slapos_cloud/ComputeNode_getSoftwareReleaseList',
        'slapos_cloud/ComputeNode_getSoftwareReleaseUrlStringList',
        'slapos_cloud/ComputeNode_getSoftwareReleaseUsage',
        'slapos_cloud/ComputeNode_getUsageReportUrl',
        'slapos_cloud/ComputeNode_init',
        'slapos_cloud/ComputePartition_getAvailableSoftwareReleaseUrlStringList',
        'slapos_cloud/ComputePartition_getCustomAllocationParameterDict',
        'slapos_cloud/ComputePartition_getInstanceTreeUrlString',
        'slapos_cloud/ComputePartition_getInstanceUrlString',
        'slapos_cloud/ComputePartition_getLastestContactedDate',
        'slapos_cloud/ComputePartition_getOwnerName',
        'slapos_cloud/ComputePartition_getOwnerUrl',
        'slapos_cloud/ComputePartition_getRelatedImageAbsoluteUrl',
        'slapos_cloud/ComputePartition_getRelatedInstanceCreationDate',
        'slapos_cloud/ComputePartition_getSoftwareType',
        'slapos_cloud/ComputePartition_isFreeForRequest',
        'slapos_cloud/ComputerNetwork_afterClone',
        'slapos_cloud/ComputerNetwork_getSoftwareInstanceAmount',
        'slapos_cloud/ComputerNetwork_getSoftwareReleaseAllocableState',
        'slapos_cloud/ERP5Type_asSecurityGroupId',
        'slapos_cloud/InstanceTree_getDefaultImageAbsoluteUrl',
        'slapos_cloud/InstanceTree_requestDestroy',
        'slapos_cloud/InstanceTree_requestStart',
        'slapos_cloud/InstanceTree_requestStop',
        'slapos_cloud/InstanceTree_requestParameterChange',
        'slapos_cloud/Organisation_afterClone',
        'slapos_cloud/Organisation_init',
        'slapos_cloud/Person_findPartition',
        'slapos_cloud/Project_getComputeNodeReferenceList',
        'slapos_cloud/Project_init',
        'slapos_cloud/Resource_zGetTrackingList',
        'slapos_cloud/SoftwareInstallation_requestDestruction',
        'slapos_cloud/SoftwareInstallation_getInstallationState',
        'slapos_cloud/SoftwareInstance_afterClone',
        'slapos_cloud/SoftwareInstance_checkPredecessorToSuccessorMigrationConsistency',
        'slapos_cloud/SoftwareInstance_getComputeNodeUrl',
        'slapos_cloud/SoftwareInstance_getComputePartitionIPv6',
        'slapos_cloud/SoftwareInstance_getDefaultImageAbsoluteUrl',
        'slapos_cloud/SoftwareInstance_getPartitionUrl',
        'slapos_cloud/SoftwareInstance_init',
        'slapos_cloud/SoftwareInstance_renameAndRequestStopAction',
        'slapos_cloud/SoftwareRelease_getRelatedNetworkList',
        'slapos_cloud/SoftwareRelease_getUsableComputeNodeList',
        'slapos_cloud/SoftwareInstance_viewRenameAndRequestDestroyAction',
        'slapos_cloud/Base_getSupportRequestInProgress',
        'slapos_cloud/SoftwareInstance_checkDuplicationOnInstanceTreeConsistency',
        'slapos_cloud/ComputerNetwork_getRelatedSoftwareReleaseList',
        'slapos_crm_monitoring/ComputeNode_checkInstanceOnCloseAllocation',
        'slapos_crm_monitoring/SiteMessage_setSlapOSUserSourceAndDestinatationList',
        'slapos_crm_monitoring/SupportRequestModule_exportMonitoringOPMLDescriptionList',
        'slapos_crm_monitoring/SupportRequestModule_getInstanceMessageList',
        'slapos_crm_monitoring/SupportRequestModule_getMonitoringOPMLDescriptionList',
        'slapos_crm_monitoring/SupportRequest_getInstanceMessageList',
        'slapos_crm_monitoring/SupportRequest_getInstanceMonitorUrl',
        'slapos_crm_monitoring/SupportRequest_getMonitorUrl',
        'slapos_crm_monitoring/SupportRequest_recheckMonitoring',
        'slapos_crm_monitoring/Event_checkCustomerAsSourceOrDestinationConsistency',
        'slapos_crm_monitoring/SupportRequest_checkCausalitySourceDestinationConsistency',
        'slapos_crm_monitoring/SupportRequest_getLastEvent',
        'slapos_crm/Person_getSubscriptionRequestFirstUnpaidInvoiceList',
        'slapos_crm/RegularisationRequest_afterClone',
        'slapos_crm/RegularisationRequest_getResourceItemList',
        'slapos_crm/RegularisationRequest_init',
        'slapos_pdm/InstanceTree_getUpgradeSubscriptionRelatedValue',
        'slapos_pdm/UpgradeDecision_afterClone',
        'slapos_pdm/UpgradeDecision_getResourceItemList',
        'slapos_pdm/UpgradeDecision_init',
        'slapos_contract/CloudContractLine_getRemainingInvoiceCredit',
        'slapos_simulation/DeliveryBuilder_selectSlapOSConfirmedInvoiceList',
        'slapos_simulation/DeliveryBuilder_selectSlapOSMovement',
        'slapos_simulation/InstanceTree_getRuleReference',
        'slapos_simulation/PackingList_getRuleReference',
        'slapos_simulation/PaymentTransaction_getRuleReference',
        'slapos_simulation/SaleInvoiceTransaction_postSlapOSGeneration',
        'slapos_simulation/SaleInvoiceTransaction_postSlapOSSaleInvoiceTransactionLineGeneration',
        'slapos_simulation/SaleInvoiceTransaction_selectSlapOSDelivery',
        'slapos_simulation/SalePackingList_postSlapOSGeneration',
        'slapos_simulation/SimulationMovement_removeBogusDeliveryLink',
        'slapos_simulation/SimulationMovement_testCommonRule',
        'slapos_simulation/SimulationMovement_testInvoiceSimulationRule',
        'slapos_simulation/SimulationMovement_testInvoiceTransactionSimulationRule',
        'slapos_simulation/SimulationMovement_testPaymentSimulationRule',
        'slapos_simulation/SimulationMovement_testTradeModelSimulationRule',
        'slapos_accounting/Base_testSlapOSValidTradeCondition',
        'slapos_accounting/OrderBuilder_generateSlapOSAggregatedMovementList',
        'slapos_accounting/OrderBuilder_selectSlapOSAggregatedDeliveryList',
        'slapos_accounting/PaymentTransaction_getExternalPaymentId',
        'slapos_accounting/PaymentTransaction_postOrderBuild',
        'slapos_accounting/SaleInvoiceTransaction_init',
        'slapos_accounting/SaleInvoiceTransaction_isTotalPriceEqualAccounting',
        'slapos_accounting/SaleInvoiceTransaction_isTotalPriceMatchingSalePackingList',
        'slapos_accounting/SaleInvoiceTransaction_isTradeModelCorrect',
        'slapos_accounting/PaymentTransaction_redirectToManualFreePayment',
        'slapos_accounting/PaymentTransaction_redirectToManualContactUsPayment',
        'slapos_accounting/SalePackingList_jumpToRelatedAggregatedSalePackingList',
        'slapos_accounting/SalePackingList_jumpToRelatedGroupedSalePackingList',
        'slapos_accounting/SalePackingList_postSlapOSAggregatedDeliveryBuilder',
        'slapos_accounting/SubscriptionRequest_getAggregatedConsumptionDelivery',
        'slapos_accounting/SubscriptionRequest_setAggregatedConsumptionDelivery',
        'slapos_configurator/BusinessConfiguration_runPostUpgradeConsistency',
        'slapos_configurator/BusinessConfiguration_setupSlapOSMasterStandardBT5',
        'slapos_consumption/Base_getConsumptionListAsODSReport',
        'slapos_consumption/Base_getResourceServiceTitleUitList',
        'slapos_consumption/Base_getUserConsumptionDetailList',
        'slapos_consumption/Base_jumpToViewLatestDayConsumption',
        'slapos_consumption/ComputeNode_getLatestCPUPercentLoad',
        'slapos_consumption/InstanceTree_getCPUStat',
        'slapos_consumption/InstanceTree_getDiskStat',
        'slapos_consumption/InstanceTree_getMemoryStat',
        'slapos_consumption/InstanceTree_getResourceConsumptionDetailList',
        'slapos_consumption/InstanceTree_getStatForResource',
        'slapos_consumption/SaleInvoiceTransaction_generateResourceConsumptionDocument',
        'slapos_consumption/SoftwareInstance_getAverageCPULoad',
        'slapos_consumption/SoftwareInstance_getLatestCPUPercentLoad',
        'slapos_consumption/SoftwareRelease_getAverageConsumedCPULoad',
        'slapos_consumption/SoftwareRelease_getAverageConsumedMemory',
        'slapos_wechat/Base_queryWechatOrderStatusByTradeNo',
        'slapos_wechat/ERP5Site_receiveWechatPaymentCallback',
        'slapos_payzen/PayzenEvent_isPaymentExpired',
        'slapos_deploy_theme/WebPage_getDeploySubstitutionMappingDict',
        'slapos_deploy_theme/WebPage_viewAsWeb',
        'slapos_deploy_theme/WebSection_getDocumentValue',
        'slapos_deploy_theme/WebSection_renderDefaultPageAsDeployScript',
        'slapos_upgrader/Base_getUpgradeBusinessTemplateList',
        'slapos_upgrader/ERP5Site_upgradeERP5CoreBusinessTemplate',
        'slapos_upgrader/ERP5Site_upgradeSlapOSTestUICoreBusinessTemplate',
        'slapos_upgrader/ERP5Site_upgradeUpgraderBusinessTemplate',
        'slapos_rss_style/SubscriptionRequest_getRSSDescription',
        'slapos_rss_style/WebSection_getLegacyMessageList',
        'slapos_subscription_request/Person_applyContractInvitation',
        'slapos_subscription_request/SubscriptionRequestModule_notifyActiveSubscriberList',
        'slapos_subscription_request/SubscriptionRequest_checkRelatedAccounting',
        'slapos_subscription_request/SubscriptionRequest_generateReservationRefoundSalePackingList',
        'slapos_subscription_request/SubscriptionRequest_getRelatedAccountingTransactionList',
        'slapos_subscription_request/SubscriptionRequest_notifyPaymentIsReady',
        'slapos_subscription_request/SubscriptionRequest_processStopped',
        'slapos_subscription_request/SubscriptionRequest_testSkippedReservationFree',
        'slapos_hal_json_style/AccountingTransaction_getPaymentStateAsHateoas',
        'slapos_hal_json_style/AcknowledgementTool_getUserUnreadAcknowledgementValueList',
        'slapos_hal_json_style/Base_getComputerToken',
        'slapos_hal_json_style/Base_getContextualHelpList',
        'slapos_hal_json_style/Base_getCriticalFeedUrl',
        'slapos_hal_json_style/Base_getFeedUrl',
        'slapos_hal_json_style/Base_getInvitationLink',
        'slapos_hal_json_style/Base_getNewsDictFromComputeNodeList',
        'slapos_hal_json_style/Base_getOpenComputeNodeList',
        'slapos_hal_json_style/Category_getCategoryChildTranslatedCompactTitleItemListAsJSON',
        'slapos_hal_json_style/Document_getNewsDict',
        'slapos_hal_json_style/ERP5Site_callbackFacebookLogin',
        'slapos_hal_json_style/ERP5Site_receiveGoogleCallback',
        'slapos_hal_json_style/Event_getAcknowledgementDict',
        'slapos_hal_json_style/InstanceTree_getConnectionParameterList',
        'slapos_hal_json_style/InstanceTree_getMonitorParameterDict',
        'slapos_hal_json_style/Item_getCurrentProjectTitle',
        'slapos_hal_json_style/Item_getCurrentSiteTitle',
        'slapos_hal_json_style/Login_edit',
        'slapos_hal_json_style/Organisation_acceptInvitation',
        'slapos_hal_json_style/Organisation_closeRelatedAssignment',
        'slapos_hal_json_style/Organisation_getAssociatedPersonList',
        'slapos_hal_json_style/Organisation_hasItem',
        'slapos_hal_json_style/PasswordTool_changeUserPassword',
        'slapos_hal_json_style/Person_getAssignmentDestinationList',
        'slapos_hal_json_style/Person_getCloudContractRelated',
        'slapos_hal_json_style/Person_requestComputeNode',
        'slapos_hal_json_style/Person_requestHateoasInstanceTree',
        'slapos_hal_json_style/Person_requestSupport',
        'slapos_hal_json_style/Project_acceptInvitation',
        'slapos_hal_json_style/Project_closeRelatedAssignment',
        'slapos_hal_json_style/Project_hasItem',
        'slapos_hal_json_style/Document_isRequesterOrOwner',
        'slapos_hal_json_style/Project_getComputeNodeTrackingList',
        'slapos_hal_json_style/SaleInvoiceTransaction_getRelatedInstanceTreeReportLineList',
        'slapos_hal_json_style/SaleInvoiceTransaction_getRelatedPaymentTransactionIntegrationId',
        'slapos_hal_json_style/SoftwareInstallation_getSoftwareReleaseInformation',
        'slapos_hal_json_style/SoftwareInstance_getReportedState',
        'slapos_hal_json_style/SoftwareRelease_requestInstanceTree',
        'slapos_hal_json_style/SoftwareRelease_requestSoftwareInstallation',
        'slapos_hal_json_style/SupportRequest_close',
        'slapos_hal_json_style/Ticket_getResourceItemListAsJSON',
        'slapos_hal_json_style/WebSection_getDocumentValue',
        'slapos_hal_json_style/WebSection_getLoginWarningMessage',
        'slapos_hal_json_style/Ticket_requestEvent',
        'slapos_hal_json_style/ComputerNetwork_getComputeNodeList',
        'slapos_hal_json_style/Base_getStatusMonitorUrl',
        'slapos_administration/ActivityTool_getDateForActivityMessage',
        'slapos_administration/ActivityTool_zGetDateForSQLDictMessage',
        'slapos_administration/ActivityTool_zGetDateForSQLQueueMessage',
        'slapos_administration/Base_checkStoredBrokenState',
        'slapos_administration/ERP5Site_cleanUnusedSecurityUid',
        'slapos_administration/ERP5Site_getSecurityUidStat',
        'slapos_administration/ERP5Site_updateAllLocalRolesOnSecurityGroupsForSlapOS',
        'slapos_administration/NotificationMessageModule_updateProductionNotificationId',
        'slapos_administration/TemplateTool_deleteObsoleteTemplateList',
        'slapos_administration/TemplateTool_unindexDeletedObjectList',
        'slapos_administration/WebPage_updateGadgetId',
        'slapos_administration/z_delete_security_uid_set_from_roles_and_users',
        'slapos_administration/z_get_used_computer_security_uid_list',
        'slapos_administration/z_get_used_group_security_uid_list',
        'slapos_administration/z_get_used_organisation_security_uid_list',
        'slapos_administration/z_get_used_project_security_uid_list',
        'slapos_administration/z_get_used_security_uid_list',
        'slapos_administration/z_get_used_shadow_security_uid_list',
        'slapos_administration/z_get_used_subscription_security_uid_list',
        'slapos_administration/z_get_used_user_security_uid_list',
        'slapos_administration/z_refresh_roles_and_users',
        'slapos_administration/z_search_unindexed_security_uid',
        'slapos_administration/z_get_uid_group_from_roles_and_users',
        'slapos_administration/SoftwareInstance_renewCertificate',
        'slapos_core/Base_updateSlapOSLocalRolesOnSecurityGroups',
        'slapos_core/ComputePartition_getSecurityCategoryFromUser',
        'slapos_core/ERP5Type_getSecurityCategoryFromAggregateRelatedSoftwareInstanceInstanceTree',
        'slapos_core/ERP5Type_getSecurityCategoryMapping',
        'slapos_core/SlaveInstance_getSecurityCategoryFromSoftwareInstance',
        'slapos_disaster_recovery/ERP5Site_checkDeletedDocumentList',
        'slapos_disaster_recovery/ERP5Site_checkLatestModifiedDocumentList',
        'slapos_disaster_recovery/ERP5Site_recoverFromRestoration',
        'slapos_disaster_recovery/ERP5Site_reindexOrUnindexDocumentList',
        'slapos_disaster_recovery/ERP5Site_unindexDeletedDocumentList',
        'slapos_base/Login_getFastExpirationReferenceList',
        'slapos_base/Login_isLoginBlocked',
        'slapos_base/Login_isPasswordExpired',
        'slapos_base/Login_notifyPasswordExpire',
        'slapos_base/Person_applyContractInvitation',
        'slapos_base/ERP5Site_getAvailableOAuthLoginList',
        'slapos_erp5/CatalogTool_checkNoneCreationDateConsistency']
      
      SlapOSTestCaseMixin.afterSetUp(self)

    def getBusinessTemplateList(self):
      # include administration for test_PythonSourceCode
      # This method is not used to install business templates in live test, but
      # we define it for CodingStyleTestCase.test_PythonSourceCode
      return ('erp5_administration', )


    def test_ReviewPythonScriptTestCoverageIgnoreList(self):
      content_dict = {}
      for test_component in self.portal.portal_components.searchFolder(
          portal_type='Test Component'):
        if "Slap" not in test_component.getId() or \
            "testSlapOSCodingStyle" in test_component.getId():
          continue
        content_dict[test_component.getId()] = test_component.getTextContent()

      self.assertNotEqual(len(content_dict), 0)

      skin_id_set = set()
      for business_template in self._getTestedBusinessTemplateValueList():
        skin_id_set.update(business_template.getTemplateSkinIdList())

      skin_id_list = list(skin_id_set)
      message_list = []
      for skin_path in self.coverage_ignore_path_list:
        skin_id, document_id = skin_path.split("/")
        if skin_id in skin_id_list:
          try:
            document = self.portal.portal_skins[skin_id][document_id]
            for _, content in content_dict.iteritems():
              if document.getId() in content:
                message_list.append(skin_path)
                break
          except KeyError:
            message_list.append(skin_path)

      self.assertEqual([], message_list)

    def test_PythonScriptTestCoverage(self):
      content_dict = {}
      for test_component in self.portal.portal_components.searchFolder(
          portal_type='Test Component'):
        if "Slap" not in test_component.getId() or \
            "testSlapOSCodingStyle" in test_component.getId():
          continue
        content_dict[test_component.getId()] = test_component.getTextContent()

      self.assertNotEqual(len(content_dict), 0)

      skin_id_set = set()
      for business_template in self._getTestedBusinessTemplateValueList():
        skin_id_set.update(business_template.getTemplateSkinIdList())

      # Init message list
      message_list = []
  
      # Test skins
      portal_skins = self.portal.portal_skins
      for skin_id in skin_id_set:
        skin = portal_skins[skin_id]
        for _, document in skin.ZopeFind(
            skin,
            obj_metatypes=('Script (Python)', 'Z SQL Method', ),
            search_sub=True):
          if document.getId().startswith("Alarm_"):
            # Alarms are tested directly, so we can safely skip
            continue

          found = 0
          for _, content in content_dict.iteritems():
            if document.getId() in content:
              found = 1
              break
          
          document_path = "%s/%s" % (skin.getId(), document.getId())
          if not found and document_path not in self.coverage_ignore_path_list:
            message_list.append(document_path)

      self.maxDiff = None
      self.assertEqual(message_list, [])

  return type("TestSlapOSCodingStyle.%s" % tested_business_template,
              (TestSlapOSCodingStyle,),
              {"getTestedBusinessTemplateList": lambda self: (tested_business_template, )})


def test_suite():
  """Generate test to check statically each business template
  """
  suite = unittest.TestSuite()

  from Products.ERP5 import ERP5Site
  portal_templates = ERP5Site.getSite().portal_templates
  bt5 = portal_templates.getInstalledBusinessTemplate("slapos_erp5")
  dependency_list = set(bt5.getTestDependencyList() + bt5.getDependencyList())

  for _, bt in portal_templates.resolveBusinessTemplateListDependency(dependency_list):
    if not bt.startswith('erp5_') or bt.startswith("erp5_interaction_drop"):
      suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase(bt)))

  suite.addTest(unittest.makeSuite(makeTestSlapOSCodingStyleTestCase('slapos_erp5')))
  return suite
