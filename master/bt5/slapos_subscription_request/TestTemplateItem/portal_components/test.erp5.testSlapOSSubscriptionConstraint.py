# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2012 Nexedi SA and Contributors. All Rights Reserved.
#
##############################################################################
from erp5.component.test.testSlapOSCloudConstraint import TestSlapOSConstraintMixin


class TestSubscriptionRequest(TestSlapOSConstraintMixin):

  def _createSubscriptionRequest(self):
    return self.portal.subscription_request_module.newContent(
        portal_type='Subscription Request')

  def test_noDestinationDecision(self):
    # Ensure workgroup is not allowed
    subscription_request = self._createSubscriptionRequest()

    message = "Arity Error for Relation ['destination_section'] and Type ('Organisation', 'Person'), arity is equal to 0 but should be between 1 and 1"
    self.assertIn(message, self.getMessageList(subscription_request))
