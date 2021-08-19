# Copyright (c) 2013 Nexedi SA and Contributors. All Rights Reserved.
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin

class TestSlapOSRequestValidationPayment(SlapOSTestCaseMixin):

  def test_alarm_software_instance_unallocated(self):
    self._makeTree()
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()

    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm(
      alarm, self.software_instance, script_name)

  def test_alarm_slave_instance_unallocated(self):
    self._makeSlaveTree()
    preference = self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()

    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm(
      alarm, self.software_instance, script_name)

  def test_alarm_software_instance_unallocated_disable_cloud_contract(self):
    self._makeTree()
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(False)
    self.tic()

    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm_not_visited(
      alarm, self.software_instance, script_name)

  def test_alarm_slave_instance_unallocated_disable_cloud_contract(self):
    self._makeSlaveTree()
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(False)
    self.tic()

    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm_not_visited(
      alarm, self.software_instance, script_name)


  def test_alarm_software_instance_allocated(self):
    self._makeTree()
    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()

    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm_not_visited(
      alarm, self.software_instance, script_name)

  def test_alarm_slave_instance_allocated(self):
    self._makeSlaveTree()

    preference =  self.portal.portal_preferences.getActiveSystemPreference()
    preference.setPreferredCloudContractEnabled(True)
    self.tic()
    self._makeComputeNode()
    self.software_instance.setAggregate(self.partition.getRelativeUrl())
    self.tic()
    
    script_name = "SoftwareInstance_requestValidationPayment"
    alarm = self.portal.portal_alarms.slapos_contract_request_validation_payment

    self._test_alarm_not_visited(
      alarm, self.software_instance, script_name)














