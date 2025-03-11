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
import six
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

      # Modified by subprojects during tests
      slapos_crm/PathTemplateItem/sale_trade_condition_module/slapos_ticket_trade_condition.xml
      slapos_payzen/PathTemplateItem/portal_secure_payments/slapos_payzen_test.xml

      # Modified during the configuration
      slapos_configurator/PathTemplateItem/business_configuration_module/slapos_master_configuration_workflow.xml
      """

      CodingStyleTestCase.coverage_ignore_path_list = [
        'erp5_interaction_drop/InvoiceTransaction_postGeneration',
        'slapos_cloud/ComputeNode_invalidateIfEmpty',
        'slapos_cloud/AllocationSupplyCell_asPredicate',
        'slapos_cloud/AllocationSupplyLine_asPredicate',
        'slapos_cloud/InstanceTree_getDefaultImageAbsoluteUrl',
        'slapos_cloud/InstanceTree_getSoftwareProduct',
        'slapos_cloud/InstanceTree_requestParameterChange',
        'slapos_cloud/OneTimeVirtualMasterAccessToken_getUserValue',
        'slapos_cloud/Project_getSoftwareProductPredicateList',
        'slapos_cloud/SoftwareInstallation_getInstallationState',
        'slapos_cloud/AlarmTool_checkComputeNodeMigrationConsistency',
        'slapos_cloud/AlarmTool_checkInstanceTreeMigrationConsistency',
        'slapos_cloud/AlarmTool_checkPredecessorToSuccessorMigrationConsistency',
        'slapos_cloud/ComputeNode_afterClone',
        'slapos_cloud/InstanceNode_afterClone',
        'slapos_cloud/RemoteNode_afterClone',
        'slapos_cloud/ComputeNode_applyComputerModel',
        'slapos_cloud/ComputeNode_getFreeComputePartitionCount',
        'slapos_cloud/ComputeNode_getSoftwareReleaseList',
        'slapos_cloud/ComputeNode_getSoftwareReleaseUrlStringList',
        'slapos_cloud/ComputeNode_getSoftwareReleaseUsage',
        'slapos_cloud/ComputeNode_getUsageReportUrl',
        'slapos_cloud/ComputeNode_init',
        'slapos_cloud/InstanceNode_init',
        'slapos_cloud/InstanceTree_updateParameterAndRequest',
        'slapos_cloud/RemoteNode_init',
        'slapos_cloud/ComputePartition_getAvailableSoftwareReleaseUrlStringList',
        'slapos_cloud/ComputePartition_getOwnerName',
        'slapos_cloud/ComputePartition_getRelatedImageAbsoluteUrl',
        'slapos_cloud/ComputePartition_getRelatedInstanceCreationDate',
        'slapos_cloud/ComputePartition_getSoftwareType',
        'slapos_cloud/ComputePartition_isFreeForRequest',
        'slapos_cloud/ComputerNetwork_afterClone',
        'slapos_cloud/ComputerNetwork_getSoftwareInstanceAmount',
        'slapos_cloud/Organisation_afterClone',
        'slapos_cloud/Organisation_init',
        'slapos_cloud/Person_findPartition',
        'slapos_cloud/Project_getComputeNodeReferenceList',
        'slapos_cloud/Project_init',
        'slapos_cloud/Resource_zGetTrackingList',
        'slapos_cloud/SoftwareInstance_afterClone',
        'slapos_cloud/SoftwareInstance_checkPredecessorToSuccessorMigrationConsistency',
        'slapos_cloud/SoftwareInstance_getComputePartitionIPv6',
        'slapos_cloud/SoftwareInstance_getDefaultImageAbsoluteUrl',
        'slapos_cloud/SoftwareInstance_init',
        'slapos_cloud/SoftwareInstance_propagateRemoteNode',
        'slapos_cloud/SoftwareInstance_renameAndRequestStopAction',
        'slapos_cloud/SoftwareRelease_getRelatedNetworkList',
        'slapos_cloud/SoftwareRelease_getUsableComputeNodeList',
        'slapos_cloud/SoftwareInstance_viewRenameAndRequestDestroyAction',
        'slapos_cloud/SoftwareInstance_checkDuplicationOnInstanceTreeConsistency',
        'slapos_cloud/ComputerNetwork_getRelatedSoftwareReleaseList',
        'slapos_crm_monitoring/SupportRequest_afterNewEvent',
        'slapos_crm/RegularisationRequest_afterClone',
        'slapos_crm/RegularisationRequest_getResourceItemList',
        'slapos_crm/RegularisationRequest_init',
        'slapos_erp5/CategoryTool_checkRegionMigrationConsistency',
        'slapos_erp5/Category_updateRelatedRegionAndExpire',
        'slapos_json_rpc_api/JSONRPCService_asJSON',
        'slapos_json_rpc_api/JSONRPCService_bangComputeNodeFromAPIDict',
        'slapos_json_rpc_api/JSONRPCService_bangSoftwareInstanceFromDict',
        'slapos_json_rpc_api/JSONRPCService_createComputeNodeCertificateRecordFromDict',
        'slapos_json_rpc_api/JSONRPCService_createComputerConsumptionTioXMLFileFromDict',
        'slapos_json_rpc_api/JSONRPCService_createSoftwareInstallation',
        'slapos_json_rpc_api/JSONRPCService_formatComputeNodeFromAPIDict',
        'slapos_json_rpc_api/JSONRPCService_getComputeNodeStatusFromDict',
        'slapos_json_rpc_api/JSONRPCService_getHateoasUrlFromDict',
        'slapos_json_rpc_api/JSONRPCService_getObjectFromData',
        'slapos_json_rpc_api/JSONRPCService_getSoftwareInstanceCertificatesAsJSON',
        'slapos_json_rpc_api/JSONRPCService_removeComputeNodeCertificateRecordFromDict',
        'slapos_json_rpc_api/JSONRPCService_requestSoftwareInstance',
        'slapos_json_rpc_api/JSONRPCService_searchComputeNodeSoftwareInstallationFromDict',
        'slapos_json_rpc_api/JSONRPCService_searchComputeNodeSoftwareInstanceFromDict',
        'slapos_json_rpc_api/JSONRPCService_searchInstanceNodeSlaveInstanceFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstallationErrorStateFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstallationReportStateFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstanceConnectionParameterFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstanceErrorStateFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstanceReportedStateFromDict',
        'slapos_json_rpc_api/JSONRPCService_updateSoftwareInstanceTitleFromDict',
        'slapos_pdm/UpgradeDecision_afterClone',
        'slapos_pdm/UpgradeDecision_getResourceItemList',
        'slapos_pdm/UpgradeDecision_init',
        'slapos_pdm/UpgradeDecision_getAggregateUrlString',
        'slapos_simulation/DeliveryBuilder_selectNonConsumptionUseSlapOSMovement',
        'slapos_simulation/DeliveryBuilder_selectSlapOSConfirmedInvoiceList',
        'slapos_simulation/DeliveryBuilder_selectSlapOSMovement',
        'slapos_simulation/HostingSubscription_getRuleReference',
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
        'slapos_accounting/Base_getDepositReceivedAccountList',
        'slapos_accounting/Entity_createCreditNoteSaleInvoiceTransactionAction',
        'slapos_accounting/Entity_getNonGroupedDepositAmountList',
        'slapos_accounting/AccountingTransactionLine_createMirrorPaymentTransactionToGroupSaleInvoice',
        'slapos_accounting/AccountingTransactionLine_getGroupingExtraParameterList',
        'slapos_accounting/OpenSaleOrder_archiveIfUnusedItem',
        'slapos_accounting/Base_getAccountForUse',
        'slapos_accounting/Entity_createPaymentTransactionAction',
        'slapos_accounting/Movement_getPriceCalculationOperandDict',
        'slapos_accounting/PaymentTransaction_acceptDepositPayment',
        'slapos_accounting/PaymentTransaction_getExternalPaymentId',
        'slapos_accounting/PaymentTransaction_postOrderBuild',
        'slapos_accounting/SaleInvoiceTransaction_getBaseCategoryDictForPrintout',
        'slapos_accounting/SaleInvoiceTransaction_init',
        'slapos_accounting/SaleInvoiceTransaction_isTotalPriceEqualAccounting',
        'slapos_accounting/SaleInvoiceTransaction_isTotalPriceMatchingSalePackingList',
        'slapos_accounting/SaleInvoiceTransaction_isTradeModelCorrect',
        'slapos_accounting/SaleOrder_applySaleTradeCondition',
        'slapos_accounting/SalePackingList_jumpToRelatedAggregatedSalePackingList',
        'slapos_accounting/SaleSupplyCell_asPredicate',
        'slapos_accounting/SaleSupplyLine_asPredicate',
        'slapos_consumption/ConsumptionDelivery_getRuleReference',
        'slapos_consumption/DeliveryBuilder_selectConsumptionMovementSlapOSMovement',
        'slapos_wechat/Base_queryWechatOrderStatusByTradeNo',
        'slapos_wechat/ERP5Site_receiveWechatPaymentCallback',
        'slapos_payzen/PayzenEvent_isPaymentExpired',
        'slapos_deploy_theme/WebPage_getDeploySubstitutionMappingDict',
        'slapos_deploy_theme/WebPage_viewAsWeb',
        'slapos_deploy_theme/WebSection_getDocumentValue',
        'slapos_deploy_theme/WebSection_renderDefaultPageAsDeployScript',
        'slapos_upgrader/AlarmTool_checkCloudContractDeletionConsistency',
        'slapos_upgrader/AlarmTool_checkContractInvitationTokenDeletionConsistency',
        'slapos_upgrader/Base_getUpgradeBusinessTemplateList',
        'slapos_upgrader/ERP5Site_upgradeERP5CoreBusinessTemplate',
        'slapos_upgrader/ERP5Site_upgradeUpgraderBusinessTemplate',
        'slapos_administration/Base_checkStoredBrokenState',
        'slapos_administration/ERP5Site_cleanUnusedSecurityUid',
        'slapos_administration/ERP5Site_getSecurityUidStat',
        'slapos_administration/NotificationMessageModule_updateProductionNotificationId',
        'slapos_administration/TemplateTool_deleteObsoleteTemplateList',
        'slapos_administration/TemplateTool_unindexDeletedObjectList',
        'slapos_administration/WebPage_updateGadgetId',
        'slapos_administration/z_delete_security_uid_set_from_roles_and_users',
        'slapos_administration/z_get_used_computer_security_uid_list',
        'slapos_administration/z_get_used_group_security_uid_list',
        'slapos_administration/z_get_used_project_security_uid_list',
        'slapos_administration/z_get_used_security_uid_list',
        'slapos_administration/z_get_used_shadow_security_uid_list',
        'slapos_administration/z_get_used_subscription_security_uid_list',
        'slapos_administration/z_get_used_user_security_uid_list',
        'slapos_administration/z_refresh_roles_and_users',
        'slapos_administration/z_search_unindexed_security_uid',
        'slapos_administration/z_get_uid_group_from_roles_and_users',
        'slapos_administration/SoftwareInstance_renewCertificate',
        'slapos_core/ERP5Type_asSecurityGroupIdSet',
        'slapos_core/ERP5User_getUserSecurityCategoryValueList',
        'slapos_base/Login_getFastExpirationReferenceList',
        'slapos_base/Login_isLoginBlocked',
        'slapos_base/Login_isPasswordExpired',
        'slapos_base/Login_notifyPasswordExpire',
        'slapos_erp5/CertificateAuthorityTool_checkCertificateAuthorityConsistency',
        'slapos_panel_compatibility/Base_getComputerToken',
        'slapos_panel_compatibility/Person_requestComputer',
        'slapos_panel/AllocationSupply_invalidateComputeNodeList',
        'slapos_panel/AllocationSupply_validateAndSupplyComputeNodeList',
        'slapos_panel/Base_addSlapOSSupportRequest',
        'slapos_panel/Base_getAuthenticatedPersonUid',
        'slapos_panel/Base_getNewsDictFromComputeNodeList',
        'slapos_panel/Base_getPaymentModeForCurrency',
        'slapos_panel/Base_getStatusMonitorUrl',
        'slapos_panel/CertificateLogin_invalidateOnSlaposPanel',
        'slapos_panel/ComputeNode_requestCertificate',
        'slapos_panel/ComputeNode_revokeCertificate',
        'slapos_panel/ComputeNode_selectSupplySoftwareProduct',
        'slapos_panel/ComputeNode_selectSupplySoftwareRelease',
        'slapos_panel/ComputerNetwork_getNewsDict',
        'slapos_panel/ComputerNetwork_invalidateOnSlaposPanel',
        'slapos_panel/Document_getNewsDict',
        'slapos_panel/Event_getAttachmentList',
        'slapos_panel/Event_getSafeSourceTitle',
        'slapos_panel/Event_getUnsafeSourceTitle',
        'slapos_panel/InstanceNode_addSlapOSAllocationSupply',
        'slapos_panel/InstanceTreeModule_selectRequestProject',
        'slapos_panel/InstanceTree_addSlapOSInstanceNode',
        'slapos_panel/InstanceTree_requestBang',
        'slapos_panel/InstanceTree_getConnectionParameterList',
        'slapos_panel/InstanceTree_getMonitorParameterDict',
        'slapos_panel/InstanceTree_getNewsDict',
        'slapos_panel/InstanceTree_requestDestroy',
        'slapos_panel/InstanceTree_requestPerson',
        'slapos_panel/InstanceTree_requestStart',
        'slapos_panel/InstanceTree_requestStop',
        'slapos_panel/InstanceTree_updateParameter',
        'slapos_panel/PaymentTransaction_redirectToManualPayment',
        'slapos_panel/Person_addSlapOSCredentialToken',
        'slapos_panel/Project_addSlapOSAllocationSupply',
        'slapos_panel/Project_addSlapOSComputeNode',
        'slapos_panel/Project_addSlapOSComputeNodeToken',
        'slapos_panel/Project_addSlapOSComputerNetwork',
        'slapos_panel/Project_addSlapOSRemoteNode',
        'slapos_panel/Project_addSlapOSSaleSupply',
        'slapos_panel/Project_addSlapOSSoftwareProduct',
        'slapos_panel/Project_getComputeNodeTrackingList',
        'slapos_panel/Project_getPayableSoftwareProductPredicateList',
        'slapos_panel/Project_getSoftwareProductPriceInformationText',
        'slapos_panel/Project_getSoftwareReleaseSchemaUrl',
        'slapos_panel/Project_redirectSlapOSComputeNodeCertificate',
        'slapos_panel/Project_selectRequestInstanceTree',
        'slapos_panel/Project_selectRequestSoftwareRelease',
        'slapos_panel/SaleSupply_invalidateOnSlaposPanel',
        'slapos_panel/SaleSupply_validateOnSlaposPanel',
        'slapos_panel/SoftwareInstallation_getNewsDict',
        'slapos_panel/SoftwareInstallation_getSoftwareReleaseInformation',
        'slapos_panel/SoftwareInstallation_requestDestruction',
        'slapos_panel/SoftwareInstance_getAllocableNodeList',
        'slapos_panel/SoftwareInstance_getAllocationInformation',
        'slapos_panel/SoftwareInstance_getConnectionParameterList',
        'slapos_panel/SoftwareInstance_getNewsDict',
        'slapos_panel/SoftwareProduct_addSlapOSSoftwareRelease',
        'slapos_panel/SoftwareProduct_addSlapOSSoftwareType',
        'slapos_panel/SubscriptionRequest_changeSlaposSubmittedPrice',
        'slapos_panel/SubscriptionRequest_jumpToPaymentPage',
        'slapos_panel/Ticket_addSlapOSEvent',
        'slapos_panel/AccountingTransactionModule_getCreateExternalPaymentTransactionList',
        'slapos_panel/AccountingTransactionModule_testCreateExternalPaymentTransactionPending',
        'slapos_panel/Base_getExternalPaymentTransactionUrl',
        'slapos_panel/Base_getSupportedExternalPaymentList',
        'slapos_panel/Base_isExternalPaymentConfigured',
        'slapos_panel/InstanceTree_getCreateDirectDepositPaymentTransactionList',
        'slapos_panel/InstanceTree_testCreateDirectDepositPaymentTransaction',
        'slapos_panel/UpgradeDecision_acceptOnSlaposPanel',
        'slapos_panel/UpgradeDecision_rejectOnSlaposPanel',
        'slapos_panel/SaleInvoiceTransaction_getInvoicePrintoutUrl',
        'slapos_panel/InstanceTree_proposeUpgradeDecision',
        'slapos_panel/InstanceTree_searchUpgradableSoftwareReleaseList',
        'slapos_panel/SoftwareInstance_getComputeNodeUrl',
        'slapos_panel_compatibility/Base_getComputerToken',
        'slapos_parameter_editor/SoftwareProductModule_updateParameterEditorTestDialog',
        'slapos_parameter_editor/SoftwareProductModule_validateParameterEditorTestDialog',
        'slapos_parameter_editor/SoftwareProductModule_validateSoftwareReleaseForParameterEditorTestDialog',
        'slapos_web_renderjs_ui/PasswordTool_changeUserPassword',
        'slapos_web_renderjs_ui/WebSection_getDocumentValue',
        'slapos_web_renderjs_ui/WebSection_getLoginWarningMessage',
        'slapos_subscription_request/SubscriptionRequest_createOpenSaleOrder',
        'slapos_subscription_request/SubscriptionRequest_init',
        'slapos_subscription_request/OpenSaleOrderCell_createDiscountSalePackingList',
        'slapos_subscription_request/SubscriptionChangeRequest_init',
        'slapos_subscription_request/Resource_createSubscriptionRequest',
        'slapos_upgrader/Base_activateObjectMigrationToRemoteVirtualMaster',
        'slapos_upgrader/Base_activateObjectMigrationToVirtualMaster',
        'slapos_upgrader/Base_deleteProcessedDocumentDuringPurge',
        'slapos_upgrader/Base_reportVirtualMasterMigration',
        'slapos_upgrader/Base_reportVirtualMasterMigration2',
        'slapos_upgrader/Base_reportVirtualMasterMigration3',
        'slapos_upgrader/Base_reportVirtualMasterMigration4',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMaster',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep2',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep3',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep4',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep5',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep6',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep7',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep8',
        'slapos_upgrader/Base_triggerFullSiteMigrationToVirtualMasterStep9',
        'slapos_upgrader/ComputeNode_checkAllocationSupplyToVirtualMaster',
        'slapos_upgrader/ComputeNode_checkSiteMigrationToVirtualMaster',
        'slapos_upgrader/ComputeNode_fixupSiteMigrationToVirtualMaster',
        'slapos_upgrader/ComputeNode_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/ComputerNetwork_checkSiteMigrationToVirtualMaster',
        'slapos_upgrader/ComputerNetwork_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/InstanceNode_checkAllocationSupplyToVirtualMaster',
        'slapos_upgrader/InstanceTree_checkSiteMigrationToVirtualMaster',
        'slapos_upgrader/InstanceTree_fixupSiteMigrationToVirtualMaster',
        'slapos_upgrader/InstanceTree_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/MailMessage_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/Note_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/OpenSaleOrder_checkSubscriptionRequestToVirtualMaster',
        'slapos_upgrader/Person_checkAssignmentToVirtualMaster',
        'slapos_upgrader/Person_checkSiteMigrationCreatePersonalVirtualMaster',
        'slapos_upgrader/ProjectModule_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/Project_checkInstanceNodeToVirtualMaster',
        'slapos_upgrader/Project_checkSiteMigrationCreateRemoteNode',
        'slapos_upgrader/Project_checkSoftwareProductToVirtualMaster',
        'slapos_upgrader/RemoteNode_checkAllocationSupplyToVirtualMaster',
        'slapos_upgrader/SiteMessage_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/SlaveInstance_triggerObjectMigrationToRemoteVirtualMaster',
        'slapos_upgrader/SlaveInstance_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/SoftwareInstallation_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/SoftwareInstance_triggerObjectMigrationToRemoteVirtualMaster',
        'slapos_upgrader/SoftwareInstance_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/SupportRequest_checkSiteMigrationToVirtualMaster',
        'slapos_upgrader/SupportRequest_triggerObjectMigrationToVirtualMaster',
        'slapos_upgrader/WebMessage_triggerObjectMigrationToVirtualMaster',
        'slapos_configurator/BusinessConfiguration_runPostUpgradeConsistency',
        'slapos_configurator/BusinessConfiguration_setupSlapOSMasterStandardBT5'
      ]

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
            for _, content in six.iteritems(content_dict):
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
          for _, content in six.iteritems(content_dict):
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
