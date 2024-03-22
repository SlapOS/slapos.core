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
    self.assertNotIn(migration_message, getMessageList(instance_nothing_to_migrate))
    self.assertNotIn(error_message, getMessageList(instance_nothing_to_migrate))

    # Migrate
    self.assertIn(migration_message, getMessageList(instance_to_migrate))
    self.assertNotIn(error_message, getMessageList(instance_to_migrate))
    instance_to_migrate.fixConsistency()
    self.assertEqual(None, instance_to_migrate.getPredecessor())
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_to_migrate.getSuccessor())
    self.assertNotIn(migration_message, getMessageList(instance_to_migrate))
    self.assertNotIn(error_message, getMessageList(instance_to_migrate))

    # Error
    self.assertNotIn(migration_message, getMessageList(instance_badly_migrated))
    self.assertIn(error_message, getMessageList(instance_badly_migrated))
    instance_badly_migrated.fixConsistency()
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_badly_migrated.getPredecessor())
    self.assertEqual(instance_nothing_to_migrate.getRelativeUrl(),
                     instance_badly_migrated.getSuccessor())
    self.assertNotIn(migration_message, getMessageList(instance_badly_migrated))
    self.assertIn(error_message, getMessageList(instance_badly_migrated))

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
    self.assertNotIn(migration_message, getMessageList(hosting_subscription_nothing_to_migrate))

    # To migrate
    self.assertIn(migration_message, getMessageList(hosting_subscription_to_migrate))
    hosting_subscription_to_migrate.fixConsistency()

    self.commit()
    self.assertTrue(hosting_subscription_to_migrate.hasActivity())

    instance_tree_module = self.portal.getDefaultModule('Instance Tree')
    migrated_instance_tree = instance_tree_module.restrictedTraverse(hosting_subscription_to_migrate_id)

    self.assertTrue(migrated_instance_tree.hasActivity())
    self.assertFalse(software_instance.hasActivity())
    self.tic()

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
    self.assertNotIn('hosting_subscription_workflow', migrated_instance_tree.workflow_history)
    self.assertNotIn(migration_message, getMessageList(migrated_instance_tree))
    self.assertEqual(migrated_instance_tree.getRelativeUrl(),
                     software_instance.getAggregate())
    self.assertEqual(1, len(self.portal.portal_catalog(uid=migrated_instance_tree.getUid())))

  def test_upgrade_computer_to_compute_node(self):
    migration_message = 'Computer must be migrated to a Compute Node'

    computer_module = self.portal.getDefaultModule('Computer')

    computer_nothing_to_migrate = computer_module.newContent(
      portal_type='Computer'
    )

    computer_to_migrate = computer_module.newContent(
      portal_type='Computer',
      quantity=99,
      bar='foo3'
    )

    # Create fake workflow history
    creation_date = DateTime('2011/11/15 11:11')
    modification_date = DateTime('2012/11/15 11:11')
    computer_to_migrate.workflow_history['edit_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': creation_date,
        'action': 'foo_action'
        }]
    computer_to_migrate.workflow_history['validation_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'validation_state': 'validated',
        'time': modification_date,
        'action': 'validate'
        }]
    computer_to_migrate.workflow_history['computer_slap_interface_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': modification_date,
        'action': 'barfoo'
        }]

    computer_partition = computer_to_migrate.newContent(
      portal_type='Computer Partition'
    )

    # Check that related object are updated
    software_installation = self.portal.software_installation_module.newContent(
      portal_type='Software Installation',
      aggregate_value=computer_to_migrate
    )
    software_instance = self.portal.software_instance_module.newContent(
      portal_type='Software Instance',
      aggregate_value=computer_partition
    )

    computer_to_migrate_id = computer_to_migrate.getId()
    computer_to_migrate_uid = computer_to_migrate.getUid()
    self.tic()

    # Nothing to migrate
    self.assertNotIn(migration_message, getMessageList(computer_nothing_to_migrate))

    # To migrate
    self.assertIn(migration_message, getMessageList(computer_to_migrate))
    computer_to_migrate.fixConsistency()

    self.commit()
    self.assertFalse(computer_to_migrate.hasActivity())

    compute_node_module = self.portal.getDefaultModule('Compute Node')
    migrated_compute_node = compute_node_module.restrictedTraverse(computer_to_migrate_id)
    migrated_computer_partition = migrated_compute_node.restrictedTraverse(computer_partition.getId())

    self.assertTrue(migrated_compute_node.hasActivity())
    self.assertFalse(computer_partition.hasActivity())
    self.assertTrue(migrated_computer_partition.hasActivity())

    self.assertEqual('Computer Partition',
                     migrated_computer_partition.getPortalType())

    self.assertFalse(software_installation.hasActivity())
    self.assertFalse(software_instance.hasActivity())
    self.tic()
    migrated_computer_partition = migrated_compute_node.restrictedTraverse(computer_partition.getId())

    self.assertEqual('Compute Node',
                     migrated_compute_node.getPortalType())
    self.assertEqual(self.portal.compute_node_module,
                     migrated_compute_node.getParentValue())
    self.assertEqual(computer_to_migrate_id,
                     migrated_compute_node.getId())
    self.assertEqual(computer_to_migrate_uid,
                     migrated_compute_node.getUid())
    self.assertEqual(99,
                     migrated_compute_node.getQuantity())
    self.assertEqual('foo3',
                     migrated_compute_node.getProperty('bar'))
    self.assertEqual('validated',
                     migrated_compute_node.getValidationState())
    self.assertEqual('draft',
                     migrated_compute_node.getSlapState())
    self.assertEqual(creation_date,
                     migrated_compute_node.getCreationDate())
    # self.assertEqual(modification_date,
    #                  migrated_compute_node.getModificationDate())
    self.assertNotIn('computer_slap_interface_workflow', migrated_compute_node.workflow_history)

    self.assertNotIn(migration_message, getMessageList(migrated_compute_node))
    self.assertEqual(migrated_compute_node.getRelativeUrl(),
                     software_installation.getAggregate())
    self.assertEqual(migrated_computer_partition.getRelativeUrl(),
                     software_instance.getAggregate())
    self.assertEqual('Compute Partition',
                     migrated_computer_partition.getPortalType())
    self.assertEqual(1, len(self.portal.portal_catalog(uid=migrated_compute_node.getUid())))
    self.assertEqual(1, len(self.portal.portal_catalog(uid=migrated_computer_partition.getUid())))


  def test_upgrade_computer_partition_to_compute_partition(self):
    migration_message = 'Computer Partition must be migrated to a Compute Partition'

    computer_module = self.portal.getDefaultModule('Computer')
    computer = computer_module.newContent(
      portal_type='Computer'
    )
    computer_partition_to_migrate = computer.newContent(
      portal_type='Computer Partition',
      quantity=99,
      bar='foo3'
    )
    computer_nothing_to_migrate = computer.newContent(
      portal_type='Computer Partition'
    )

    # Create fake workflow history
    creation_date = DateTime('2011/11/15 11:11')
    modification_date = DateTime('2012/11/15 11:11')
    computer_partition_to_migrate.workflow_history['edit_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'state': 'current',
        'time': creation_date,
        'action': 'foo_action'
        }]
    computer_partition_to_migrate.workflow_history['validation_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'validation_state': 'validated',
        'time': modification_date,
        'action': 'validate'
        }]
    computer_partition_to_migrate.workflow_history['computer_partition_slap_interface_workflow'] = [{
        'comment':'Fake history',
        'error_message': '',
        'actor': 'ERP5TypeTestCase',
        'slap_state': 'draft',
        'time': modification_date,
        'action': 'barfoo'
        }]

    self.tic()

    # Nothing to migrate
    self.assertNotIn(migration_message, getMessageList(computer_nothing_to_migrate))

    # To migrate
    self.assertIn(migration_message, getMessageList(computer_partition_to_migrate))
    computer_partition_to_migrate.fixConsistency()

    self.commit()
    migrated_computer_partition = computer.restrictedTraverse(computer_partition_to_migrate.getId())
    self.assertTrue(migrated_computer_partition.hasActivity())

    self.tic()

    self.assertEqual('Compute Partition',
                     migrated_computer_partition.getPortalType())
    self.assertEqual(99,
                     migrated_computer_partition.getQuantity())
    self.assertEqual('foo3',
                     migrated_computer_partition.getProperty('bar'))
    self.assertEqual('validated',
                     migrated_computer_partition.getValidationState())
    self.assertEqual('draft',
                     migrated_computer_partition.getSlapState())
    self.assertEqual(creation_date,
                     migrated_computer_partition.getCreationDate())
    # self.assertEqual(modification_date,
    #                  migrated_compute_node.getModificationDate())
    self.assertNotIn('computer_partition_slap_interface_workflow', migrated_computer_partition.workflow_history)

    self.assertNotIn(migration_message, getMessageList(computer_partition_to_migrate))
    self.assertEqual(1, len(self.portal.portal_catalog(uid=migrated_computer_partition.getUid())))

