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


class TestSlapOSCloudUpgrader(SlapOSTestCaseMixin):
  def check_upgrade_instance_predecessor(self, portal_type):
    error_message = 'Error: Instance has both predecessor and successor categories'
    migration_message = 'Instance has predecessor categories not yet migrated to successor categories'

    module = self.portal.getDefaultModule(portal_type)
    instance_nothing_to_migrate = module.newContent(
      portal_type=portal_type
    )
    instance_to_migrate = module.newContent(
      portal_type=portal_type,
      predecessor_value=instance_nothing_to_migrate
    )
    instance_badly_migrated = module.newContent(
      portal_type=portal_type,
      predecessor_value=instance_nothing_to_migrate,
      successor_value=instance_nothing_to_migrate
    )

    # Nothing to migrate
    self.assertFalse(migration_message in getMessageList(instance_nothing_to_migrate))
    self.assertFalse(error_message in getMessageList(instance_nothing_to_migrate))

    # Migrate
    self.assertTrue(migration_message in getMessageList(instance_to_migrate))
    self.assertFalse(error_message in getMessageList(instance_to_migrate))
    instance_to_migrate.fixConsistency()
    self.assertEqual(None, instance_to_migrate.getPredecessor())
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_to_migrate.getSuccessor())
    self.assertFalse(migration_message in getMessageList(instance_to_migrate))
    self.assertFalse(error_message in getMessageList(instance_to_migrate))

    # Error
    self.assertFalse(migration_message in getMessageList(instance_badly_migrated))
    self.assertTrue(error_message in getMessageList(instance_badly_migrated))
    instance_badly_migrated.fixConsistency()
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_badly_migrated.getPredecessor())
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_badly_migrated.getSuccessor())
    self.assertFalse(migration_message in getMessageList(instance_badly_migrated))
    self.assertTrue(error_message in getMessageList(instance_badly_migrated))

  def test_upgrade_software_instance_predecessor(self):
    return self.check_upgrade_instance_predecessor('Software Instance')

  def test_upgrade_instance_tree_predecessor(self):
    return self.check_upgrade_instance_predecessor('Instance Tree')

  def test_upgrade_hosting_subscription_to_instance_tree(self):
    migration_message = 'Hosting Subscription must be migrated to an Instance Tree'

    hosting_subscription_module = self.portal.getDefaultModule('Hosting Subscription')

    hosting_subscription_nothing_to_migrate = hosting_subscription_module.newContent(
      portal_type='Hosting Subscription'
    )

    hosting_subscription_to_migrate = hosting_subscription_module.newContent(
      portal_type='Hosting Subscription',
      sla_xml='foo',
      bar='foo3',
      category_list=['successor/foo1', 'predecessor/foo2']
    )

    # Create fake workflow history
    creation_date = DateTime('2011/11/15 11:11')
    modification_date = DateTime('2012/11/15 11:11')
    hosting_subscription_to_migrate.workflow_history['edit_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': creation_date,
        'action': 'foo_action'
        }]
    hosting_subscription_to_migrate.workflow_history['hosting_subscription_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'validation_state': 'validated',
        'time': modification_date,
        'action': 'validate'
        }]

    software_instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      aggregate_value=hosting_subscription_to_migrate
    )
    hosting_subscription_to_migrate_id = hosting_subscription_to_migrate.getId()
    hosting_subscription_to_migrate_uid = hosting_subscription_to_migrate.getUid()
    self.tic()

    # Nothing to migrate
    self.assertTrue(migration_message in getMessageList(hosting_subscription_nothing_to_migrate))

    # To migrate
    self.assertTrue(migration_message in getMessageList(hosting_subscription_to_migrate))
    hosting_subscription_to_migrate.fixConsistency()
    self.tic()

    instance_tree_module = self.portal.getDefaultModule('Instance Tree')
    migrated_instance_tree = instance_tree_module.restrictedTraverse(hosting_subscription_to_migrate_id)
    self.assertEqual('Instance Tree',
                     migrated_instance_tree.getPortalType())
    self.assertEqual(self.portal.instance_tree_module,
                     migrated_instance_tree.getParentValue())
    self.assertEqual(hosting_subscription_to_migrate_id,
                     migrated_instance_tree.getId())
    self.assertEqual(hosting_subscription_to_migrate_uid,
                     migrated_instance_tree.getUid())
    self.assertEqual('foo',
                     migrated_instance_tree.getSlaXml())
    self.assertEqual('foo1',
                     migrated_instance_tree.getSuccessor())
    self.assertEqual('foo2',
                     migrated_instance_tree.getPredecessor())
    self.assertEqual('foo3',
                     migrated_instance_tree.getProperty('bar'))
    self.assertEqual('validated',
                     migrated_instance_tree.getValidationState())
    self.assertEqual(creation_date,
                     migrated_instance_tree.getCreationDate())
    # self.assertEqual(modification_date,
    #                  migrated_instance_tree.getModificationDate())
    self.assertFalse('hosting_subscription_workflow' in migrated_instance_tree.workflow_history)
    self.assertFalse(migration_message in getMessageList(migrated_instance_tree))
    self.assertEqual(migrated_instance_tree.getRelativeUrl(),
                     software_instance.getAggregate())
