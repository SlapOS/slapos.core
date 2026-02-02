# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2022 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSERP5VirtualMasterScenario import TestSlapOSVirtualMasterScenarioMixin
from erp5.component.test.SlapOSTestCaseMixin import PinnedDateTime, TemporaryAlarmScript
from DateTime import DateTime

class testSlapOSConsumptionScenarioForInstance(TestSlapOSVirtualMasterScenarioMixin):

  def test_validate_software_instance(self):
    with PinnedDateTime(self,  DateTime('2024/12/17')):
      instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )

    with PinnedDateTime(self,  DateTime('2024/12/17 01:00')):
      with TemporaryAlarmScript(self.portal, 'Base_generateConsumptionDeliveryForValidatedInstance'):
        instance.validate()
        self.tic()

    self.assertEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self,  DateTime('2024/12/17 01:01')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
      instance.edit()
      self.tic()


    with PinnedDateTime(self,  DateTime('2024/12/17 02:01')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
      instance.edit()
      self.tic()

    self.assertEqual(instance.getExpirationDate(), None)
    with PinnedDateTime(self,  DateTime('2024/12/17 03:01')):
      instance.setExpirationDate(DateTime() + 1)
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )
    self.assertNotEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self,  DateTime('2024/12/17 03:01') + 1):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_validated_instance,
        instance,
        'Base_generateConsumptionDeliveryForValidatedInstance'
      )

  def test_invalidated_software_instance(self):

    with PinnedDateTime(self,  DateTime('2024/12/17')):
      instance = self.portal.software_instance_module.newContent(portal_type='Software Instance')
      self.portal.portal_workflow._jumpToStateFor(instance, 'invalidated')
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 01:00')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      # To clean last edit comment
      instance.edit()
      self.tic()

    self.assertEqual(instance.getExpirationDate(), None)

    with PinnedDateTime(self, DateTime('2024/12/17 02:00')):
      self._test_alarm(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      instance.edit(expiration_date = DateTime())
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 03:00')):
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
      instance.edit()
      self.tic()

    with PinnedDateTime(self, DateTime('2024/12/17 04:00')):
      self._test_alarm_not_visited(
        self.portal.portal_alarms.slapos_accounting_generate_consumption_delivery_for_invalidated_instance,
        instance,
        'Base_generateConsumptionDeliveryForInvalidatedInstance'
      )
