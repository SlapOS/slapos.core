# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################

from erp5.component.test.testSlapOSSubscriptionScenario import TestSlapOSSubscriptionScenarioMixin

class TestSlapOSSubscriptionChineseScenario(TestSlapOSSubscriptionScenarioMixin):

  def afterSetUp(self):
    TestSlapOSSubscriptionScenarioMixin.afterSetUp(self)
    self.expected_individual_price_without_tax = 1573.3333333333335
    self.expected_individual_price_with_tax = 1888.00

  def createSubscriptionCondition(self, slave=False):
    self.subscription_condition = self.portal.subscription_condition_module.newContent(
      portal_type="Subscription Condition",
      title="TestSubscriptionChineseScenario",
      short_tile="Test Your Chinese Scenario",
      description="This is a Chinese test",
      url_string=self.generateNewSoftwareReleaseUrl(),
      root_slave=slave,
      price=1888.00,
      resource="currency_module/CNY",
      default_source_reference="default",
      reference="rapidvm%s" % self.new_id,
      # Aggregate and Follow up to web pages for product description and
      # Terms of service
      sla_xml='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      text_content='<?xml version="1.0" encoding="utf-8"?>\n<instance>\n</instance>',
      user_input={}
    )
    self.subscription_condition.validate()
    self.subscription_condition.updateLocalRolesOnSecurityGroups()
    self.tic()

  def test_subscription_scenario(self):
    self._test_subscription_scenario(amount=1)

  def test_subscription_with_3_vms_scenario(self):
    self._test_subscription_scenario(amount=3)

  def test_subscription_scenario_with_reversal_transaction(self):
    self._test_subscription_scenario_with_reversal_transaction(amount=1)

  def test_two_subscription_scenario(self):
    self._test_two_subscription_scenario(amount=1)
