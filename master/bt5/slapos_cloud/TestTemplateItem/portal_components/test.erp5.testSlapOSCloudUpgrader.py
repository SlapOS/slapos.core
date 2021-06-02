# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2021 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin


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

  def test_upgrade_hosting_subscription_predecessor(self):
    return self.check_upgrade_instance_predecessor('Hosting Subscription')
