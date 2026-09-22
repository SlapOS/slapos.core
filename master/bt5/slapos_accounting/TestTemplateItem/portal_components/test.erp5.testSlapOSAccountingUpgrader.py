# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2021 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
from DateTime import DateTime


def getMessageList(instance):
  return [str(m.getMessage()) for m in instance.checkConsistency()]


class TestSlapOSAccountingUpgrader(SlapOSTestCaseMixin):
  def test_upgrade_compute_node_trade_condition_type(self):
    # Testing:
    # - SaleTradeCondition_checkComputeNodeTradeConditionTypeMigrationConsistency
    # - SaleTradeCondition_archiveIfComputeNodeTradeConditionType
    # - OpenSaleOrder_archiveIfComputeNodeTradeConditionType
    # - MISSING: AlarmTool_checkSaleTradeConditionComputeNodeTradeConditionTypeMigrationConsistency
    migration_message = 'trade_condition_type/compute_node must expire'

    portal_type = 'Sale Trade Condition'
    module = self.portal.getDefaultModule(portal_type)
    trade_condition_nothing_to_migrate = module.newContent(
      portal_type=portal_type,
    )
    self.portal.portal_workflow._jumpToStateFor(trade_condition_nothing_to_migrate, 'validated')
    trade_condition_to_migrate = module.newContent(
      portal_type=portal_type,
      trade_condition_type='compute_node',
    )
    self.portal.portal_workflow._jumpToStateFor(trade_condition_to_migrate, 'validated')
    specialising1_trade_condition_to_migrate = module.newContent(
      portal_type=portal_type,
      trade_condition_type='default',
      specialise_value=trade_condition_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(specialising1_trade_condition_to_migrate, 'validated')
    specialising2_trade_condition_to_migrate = module.newContent(
      portal_type=portal_type,
      specialise_value=specialising1_trade_condition_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(specialising2_trade_condition_to_migrate, 'validated')

    portal_type = 'Open Sale Order'
    module = self.portal.getDefaultModule(portal_type)
    open_order_nothing_to_migrate = module.newContent(
      portal_type=portal_type,
      ledger='automated',
      specialise_value=trade_condition_nothing_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(open_order_nothing_to_migrate, 'validated')
    open_order1_to_migrate = module.newContent(
      portal_type=portal_type,
      ledger='automated',
      specialise_value=trade_condition_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(open_order1_to_migrate, 'validated')
    open_order2_to_migrate = module.newContent(
      portal_type=portal_type,
      ledger='automated',
      specialise_value=specialising1_trade_condition_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(open_order2_to_migrate, 'validated')
    open_order3_to_migrate = module.newContent(
      portal_type=portal_type,
      ledger='automated',
      specialise_value=specialising2_trade_condition_to_migrate,
    )
    self.portal.portal_workflow._jumpToStateFor(open_order3_to_migrate, 'validated')

    # Nothing to migrate
    self.assertNotIn(migration_message, getMessageList(trade_condition_nothing_to_migrate))

    # Nothing to directly migrate
    self.assertNotIn(migration_message, getMessageList(specialising1_trade_condition_to_migrate))
    self.assertNotIn(migration_message, getMessageList(specialising2_trade_condition_to_migrate))

    # Migrate
    self.assertIn(migration_message, getMessageList(trade_condition_to_migrate))
    self.tic()
    trade_condition_to_migrate.fixConsistency()
    self.tic()
    self.assertNotEqual(None, trade_condition_to_migrate.getExpirationDate())
    self.assertNotIn(migration_message, getMessageList(trade_condition_to_migrate))

    # Specialising trade condition was also migrated
    self.assertNotEqual(None, specialising1_trade_condition_to_migrate.getExpirationDate())
    self.assertNotEqual(None, specialising2_trade_condition_to_migrate.getExpirationDate())
    self.assertEqual(None, trade_condition_nothing_to_migrate.getExpirationDate())

    # Open Order were migrated
    self.assertEqual(None, open_order_nothing_to_migrate.getStopDate())
    self.assertEqual('validated', open_order_nothing_to_migrate.getValidationState())

    self.assertNotEqual(None, open_order1_to_migrate.getStopDate())
    self.assertEqual('archived', open_order1_to_migrate.getValidationState())
    self.assertNotEqual(None, open_order2_to_migrate.getStopDate())
    self.assertEqual('archived', open_order2_to_migrate.getValidationState())
    self.assertNotEqual(None, open_order3_to_migrate.getStopDate())
    self.assertEqual('archived', open_order3_to_migrate.getValidationState())

  def test_tioxml_document_slapos_consumption_document_workflow_migration(self):
    # Testing:
    # - ComputerConsumptionTioXMLFile_checkWorkflowHistoryMigrationConsistency
    # - MISSING: AlarmTool_checkComputerConsumptionTioXMLFileWorkflowHistoryMigrationConsistency
    migration_message = 'Computer Consumption TioXML File workflow must be migrated'

    tioxml_module = self.portal.getDefaultModule('Computer Consumption TioXML File')

    tioxml_nothing_to_migrate = tioxml_module.newContent(
      portal_type='Computer Consumption TioXML File'
    )

    tioxml_to_migrate = tioxml_module.newContent(
      portal_type='Computer Consumption TioXML File',
    )

    # Create fake workflow history
    creation_date = DateTime('2011/11/15 11:11')
    modification_date = DateTime('2012/11/15 11:11')
    tioxml_to_migrate.workflow_history['edit_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': creation_date,
        'action': 'foo_action'
        }]
    tioxml_to_migrate.workflow_history['document_publication_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'validation_state': 'submitted',
        'time': modification_date,
        'action': 'submit'
        }]
    tioxml_to_migrate.workflow_history.pop('slapos_consumption_document_workflow')

    self.tic()

    # Nothing to migrate
    self.assertNotIn(migration_message, getMessageList(tioxml_nothing_to_migrate))

    # To migrate
    self.assertIn(migration_message, getMessageList(tioxml_to_migrate))
    tioxml_to_migrate.fixConsistency()

    self.commit()
    self.assertTrue(tioxml_to_migrate.hasActivity())

    self.tic()

    self.assertNotIn('document_publication_workflow', tioxml_to_migrate.workflow_history)
    self.assertEqual('submitted', tioxml_to_migrate.getValidationState())
    self.assertNotIn(migration_message, getMessageList(tioxml_to_migrate))
